"""
Unit tests for TF-IDF cosine similarity and explanation output.
"""

from apps.insights.nlp.similarity import (
    analyse_text_similarity,
    build_target_profile_text,
    score_label_for,
    target_terms_from_text,
)


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


def test_score_label_for_thresholds() -> None:
    """Score labels should map consistently to score thresholds."""
    assert score_label_for(0.8) == "Excellent match"
    assert score_label_for(0.5) == "Strong match"
    assert score_label_for(0.25) == "Partial match"
    assert score_label_for(0.1) == "Low match"


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
