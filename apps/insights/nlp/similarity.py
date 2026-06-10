"""
TF-IDF and cosine similarity utilities for Trackly job-fit insights.
"""

from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from apps.insights.nlp.text_processing import preprocess_text, preprocess_tokens

PIPELINE_VERSION = "nltk-tfidf-cosine-v1"


@dataclass(frozen=True)
class TextSimilarityResult:
    """Structured result returned by the retrieval-style similarity pipeline."""

    clean_job_text: str
    clean_target_text: str
    extracted_terms: list[str]
    top_overlapping_terms: list[str]
    top_overlapping_weighted_terms: list[dict[str, float | str]]
    missing_target_terms: list[str]
    missing_weighted_target_terms: list[dict[str, float | str]]
    similarity_score: float
    score_label: str
    explanation: str


def score_label_for(similarity_score: float) -> str:
    """Return a human-readable score label for a similarity score."""
    if similarity_score >= 0.75:
        return "Excellent match"
    if similarity_score >= 0.5:
        return "Strong match"
    if similarity_score >= 0.25:
        return "Partial match"
    return "Low match"


def build_target_profile_text(
    *,
    title: str,
    description: str,
    keywords: list[str],
) -> str:
    """Build the text document used to represent a target role profile."""
    keyword_text = " ".join(keywords)
    parts = [title, description, keyword_text]
    return "\n".join(part for part in parts if part)


def extract_weighted_terms(
    *,
    feature_names,
    vector,
    limit: int,
) -> list[str]:
    """Return top terms from a single TF-IDF vector."""
    weights = vector.toarray()[0]
    weighted_terms = [
        (feature_names[index], weight)
        for index, weight in enumerate(weights)
        if weight > 0
    ]
    ranked_terms = sorted(weighted_terms, key=lambda item: (-item[1], item[0]))
    return [term for term, _weight in ranked_terms[:limit]]


def extract_top_overlapping_terms(
    *,
    feature_names,
    job_vector,
    target_vector,
    limit: int,
) -> list[str]:
    """Return high-value terms that appear in both job and target vectors."""
    weighted_terms = extract_top_overlapping_weighted_terms(
        feature_names=feature_names,
        job_vector=job_vector,
        target_vector=target_vector,
        limit=limit,
    )
    return [str(item["term"]) for item in weighted_terms]


def extract_top_overlapping_weighted_terms(
    *,
    feature_names,
    job_vector,
    target_vector,
    limit: int,
) -> list[dict[str, float | str]]:
    """Return top overlapping terms with their TF-IDF contribution weights."""
    job_weights = job_vector.toarray()[0]
    target_weights = target_vector.toarray()[0]
    overlapping_terms = []

    for index, term in enumerate(feature_names):
        if job_weights[index] > 0 and target_weights[index] > 0:
            # Multiplying weights favours terms that are important in both texts.
            combined_weight = job_weights[index] * target_weights[index]
            overlapping_terms.append(
                (
                    term,
                    float(job_weights[index]),
                    float(target_weights[index]),
                    float(combined_weight),
                )
            )

    ranked_terms = sorted(overlapping_terms, key=lambda item: (-item[3], item[0]))
    return [
        {
            "term": term,
            "job_weight": round(job_weight, 4),
            "target_weight": round(target_weight, 4),
            "overlap_weight": round(overlap_weight, 4),
        }
        for term, job_weight, target_weight, overlap_weight in ranked_terms[:limit]
    ]


def extract_missing_target_terms(
    *,
    feature_names,
    job_vector,
    target_vector,
    limit: int,
) -> list[str]:
    """Return high-value target terms that are absent from the job text."""
    weighted_terms = extract_missing_weighted_target_terms(
        feature_names=feature_names,
        job_vector=job_vector,
        target_vector=target_vector,
        limit=limit,
    )
    return [str(item["term"]) for item in weighted_terms]


def extract_missing_weighted_target_terms(
    *,
    feature_names,
    job_vector,
    target_vector,
    limit: int,
) -> list[dict[str, float | str]]:
    """Return missing target terms with their target-side TF-IDF weights."""
    job_weights = job_vector.toarray()[0]
    target_weights = target_vector.toarray()[0]
    missing_terms = []

    for index, term in enumerate(feature_names):
        if target_weights[index] > 0 and job_weights[index] == 0:
            missing_terms.append((term, float(target_weights[index])))

    ranked_terms = sorted(missing_terms, key=lambda item: (-item[1], item[0]))
    return [
        {
            "term": term,
            "target_weight": round(target_weight, 4),
        }
        for term, target_weight in ranked_terms[:limit]
    ]


def build_explanation(
    *,
    score_label: str,
    top_overlapping_terms: list[str],
    missing_target_terms: list[str],
) -> str:
    """Build a concise explanation from TF-IDF overlap evidence."""
    if top_overlapping_terms:
        overlap_text = ", ".join(top_overlapping_terms)
    else:
        overlap_text = "no high-value target terms"

    if missing_target_terms:
        missing_text = ", ".join(missing_target_terms)
    else:
        missing_text = "no major target terms"

    return (
        f"{score_label}: this job description overlaps with your target profile "
        f"on {overlap_text}. Missing or weaker target terms include {missing_text}."
    )


def analyse_text_similarity(
    *,
    job_text: str,
    target_text: str,
    extracted_term_limit: int = 12,
    explanation_term_limit: int = 8,
) -> TextSimilarityResult:
    """Compare job text and target profile text using TF-IDF cosine similarity."""
    clean_job_text = preprocess_text(job_text)
    clean_target_text = preprocess_text(target_text)

    if not clean_job_text or not clean_target_text:
        score_label = "Low match"
        explanation = build_explanation(
            score_label=score_label,
            top_overlapping_terms=[],
            missing_target_terms=[],
        )
        return TextSimilarityResult(
            clean_job_text=clean_job_text,
            clean_target_text=clean_target_text,
            extracted_terms=[],
            top_overlapping_terms=[],
            top_overlapping_weighted_terms=[],
            missing_target_terms=[],
            missing_weighted_target_terms=[],
            similarity_score=0.0,
            score_label=score_label,
            explanation=explanation,
        )

    vectorizer = TfidfVectorizer(
        lowercase=False,
        ngram_range=(1, 2),
        token_pattern=r"(?u)\b[a-z][a-z0-9+#.-]{1,}\b",
    )
    matrix = vectorizer.fit_transform([clean_job_text, clean_target_text])
    feature_names = vectorizer.get_feature_names_out()
    job_vector = matrix[0:1]
    target_vector = matrix[1:2]

    similarity_score = round(
        float(cosine_similarity(job_vector, target_vector)[0][0]), 2
    )
    score_label = score_label_for(similarity_score)
    extracted_terms = extract_weighted_terms(
        feature_names=feature_names,
        vector=job_vector,
        limit=extracted_term_limit,
    )
    top_overlapping_weighted_terms = extract_top_overlapping_weighted_terms(
        feature_names=feature_names,
        job_vector=job_vector,
        target_vector=target_vector,
        limit=explanation_term_limit,
    )
    top_overlapping_terms = [
        str(item["term"]) for item in top_overlapping_weighted_terms
    ]
    missing_weighted_target_terms = extract_missing_weighted_target_terms(
        feature_names=feature_names,
        job_vector=job_vector,
        target_vector=target_vector,
        limit=explanation_term_limit,
    )
    missing_target_terms = [str(item["term"]) for item in missing_weighted_target_terms]
    explanation = build_explanation(
        score_label=score_label,
        top_overlapping_terms=top_overlapping_terms,
        missing_target_terms=missing_target_terms,
    )

    return TextSimilarityResult(
        clean_job_text=clean_job_text,
        clean_target_text=clean_target_text,
        extracted_terms=extracted_terms,
        top_overlapping_terms=top_overlapping_terms,
        top_overlapping_weighted_terms=top_overlapping_weighted_terms,
        missing_target_terms=missing_target_terms,
        missing_weighted_target_terms=missing_weighted_target_terms,
        similarity_score=similarity_score,
        score_label=score_label,
        explanation=explanation,
    )


def target_terms_from_text(text: str) -> list[str]:
    """Return unique processed target terms for diagnostics and tests."""
    return sorted(set(preprocess_tokens(text)))
