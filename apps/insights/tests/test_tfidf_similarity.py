"""
Unit tests for TF-IDF cosine similarity and explanation output.
"""

import pytest

from apps.insights.nlp import similarity
from apps.insights.nlp.similarity import (
    PIPELINE_VERSION,
    analyse_text_similarity,
    build_target_profile_text,
    score_label_for,
    target_terms_from_text,
)

LOW_VALUE_TERMS = {"and", "about", "target", "role", "using"}


def assert_low_value_terms_excluded(terms: list[str]) -> None:
    """Assert that low-value terms do not appear as terms or n-gram parts."""
    for term in terms:
        assert term not in LOW_VALUE_TERMS
        assert LOW_VALUE_TERMS.isdisjoint(term.split())


def test_related_job_scores_higher_than_unrelated_job() -> None:
    """Related job text should score higher than unrelated job text."""
    target_text = build_target_profile_text(
        title="Graduate Backend Engineer",
        description="Python Django APIs PostgreSQL Docker testing",
        keywords=["python", "django", "api", "postgresql", "docker", "testing"],
    )
    related = analyse_text_similarity(
        job_text="Python Django REST API PostgreSQL Docker testing role",
        target_text=target_text,
    )
    unrelated = analyse_text_similarity(
        job_text="Graphic design illustration branding and photography",
        target_text=target_text,
    )

    assert related.similarity_score > unrelated.similarity_score


def test_similarity_result_contains_overlapping_terms() -> None:
    """Similarity output should include overlapping high-value terms."""
    result = analyse_text_similarity(
        job_text="Python Django REST API testing",
        target_text="Python Django REST API PostgreSQL Docker testing",
    )

    assert "python" in result.top_overlapping_terms
    assert "django" in result.top_overlapping_terms


def test_similarity_result_ranks_explanation_terms_deterministically() -> None:
    """Explanation terms should be ranked by TF-IDF weight with stable tie breaks."""
    result = analyse_text_similarity(
        job_text="Alpha Beta",
        target_text="Alpha Beta Gamma Delta",
        explanation_term_limit=10,
    )

    assert result.top_overlapping_terms == ["alpha", "alpha beta", "beta"]
    assert result.missing_target_terms == [
        "beta gamma",
        "delta",
        "gamma",
        "gamma delta",
    ]
    assert result.explanation == (
        "Strong match: this job description overlaps with your target profile "
        "on alpha, alpha beta, beta. Missing or weaker target terms include "
        "beta gamma, delta, gamma, gamma delta."
    )


def test_similarity_result_contains_missing_target_terms() -> None:
    """Similarity output should include target terms absent from job text."""
    result = analyse_text_similarity(
        job_text="Python Django testing",
        target_text="Python Django PostgreSQL Docker testing",
    )

    assert "postgresql" in result.missing_target_terms
    assert "docker" in result.missing_target_terms


def test_similarity_result_contains_extracted_terms() -> None:
    """Similarity output should include weighted terms from the job text."""
    result = analyse_text_similarity(
        job_text="Python Django REST API testing",
        target_text="Python Django testing",
    )

    assert result.extracted_terms
    assert "python" in result.extracted_terms


def test_similarity_pipeline_uses_sklearn_tfidf_cosine_contract(monkeypatch) -> None:
    """The pipeline contract should use scikit-learn TF-IDF and cosine scoring."""
    real_vectorizer = similarity.TfidfVectorizer
    real_cosine_similarity = similarity.cosine_similarity
    calls = {}

    def tracking_vectorizer(*args, **kwargs):
        calls["vectorizer_kwargs"] = kwargs
        return real_vectorizer(*args, **kwargs)

    def tracking_cosine_similarity(job_vector, target_vector):
        calls["cosine_similarity"] = True
        return real_cosine_similarity(job_vector, target_vector)

    monkeypatch.setattr(similarity, "TfidfVectorizer", tracking_vectorizer)
    monkeypatch.setattr(similarity, "cosine_similarity", tracking_cosine_similarity)

    result = analyse_text_similarity(
        job_text="Python Django REST API testing",
        target_text="Python Django PostgreSQL testing",
    )

    assert PIPELINE_VERSION == "nltk-tfidf-cosine-v1"
    assert calls["vectorizer_kwargs"] == {
        "lowercase": False,
        "ngram_range": (1, 2),
        "token_pattern": r"(?u)\b[a-z][a-z0-9+#.-]{1,}\b",
    }
    assert calls["cosine_similarity"] is True
    assert result.similarity_score > 0


def test_similarity_evidence_excludes_low_value_terms() -> None:
    """Extracted, overlapping, and missing terms should exclude stop words."""
    result = analyse_text_similarity(
        job_text="Target role using Python and Django about APIs",
        target_text="Target role using Python Django about PostgreSQL",
    )

    assert "python" in result.extracted_terms
    assert "python" in result.top_overlapping_terms
    assert "postgresql" in result.missing_target_terms
    assert_low_value_terms_excluded(result.extracted_terms)
    assert_low_value_terms_excluded(result.top_overlapping_terms)
    assert_low_value_terms_excluded(result.missing_target_terms)


def test_similarity_output_is_deterministic_for_same_input() -> None:
    """Repeated analysis with the same input should produce the same result."""
    first = analyse_text_similarity(
        job_text="Python Django REST API testing",
        target_text="Python Django REST API PostgreSQL",
    )
    second = analyse_text_similarity(
        job_text="Python Django REST API testing",
        target_text="Python Django REST API PostgreSQL",
    )

    assert first == second


@pytest.mark.parametrize(
    ("similarity_score", "expected_label"),
    [
        (0.75, "Excellent match"),
        (0.74, "Strong match"),
        (0.5, "Strong match"),
        (0.49, "Partial match"),
        (0.25, "Partial match"),
        (0.24, "Low match"),
        (0.0, "Low match"),
    ],
)
def test_score_label_for_thresholds(
    similarity_score: float,
    expected_label: str,
) -> None:
    """Score labels should map consistently to deterministic thresholds."""
    assert score_label_for(similarity_score) == expected_label


def test_explanation_includes_overlap_and_missing_terms() -> None:
    """Generated explanations should include evidence terms."""
    result = analyse_text_similarity(
        job_text="Python Django testing",
        target_text="Python Django Docker testing",
    )

    assert "Python" not in result.explanation
    assert "python" in result.explanation
    assert "docker" in result.explanation


def test_target_terms_from_text_returns_unique_terms() -> None:
    """Target term diagnostics should return unique processed terms."""
    terms = target_terms_from_text("Python Python Django APIs")

    assert terms.count("python") == 1
    assert "django" in terms
