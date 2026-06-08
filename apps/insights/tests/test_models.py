"""Model tests for Trackly job insights."""

import pytest
from django.core.exceptions import ValidationError

from apps.insights.factories import JobInsightFactory, TargetRoleProfileFactory
from apps.insights.models import JobInsight, TargetRoleProfile
from apps.jobs.factories import JobApplicationFactory
from apps.users.factories import UserFactory


@pytest.mark.django_db
def test_target_role_profile_has_readable_string_representation() -> None:
    """A target role profile should render as its title."""
    profile = TargetRoleProfileFactory(title="Backend Engineer")

    assert str(profile) == "Backend Engineer"


@pytest.mark.django_db
def test_target_role_profile_persists_keywords() -> None:
    """Target role profiles should persist cleaned lowercase keywords."""
    profile = TargetRoleProfileFactory(keywords=["Python", " Django ", "python"])

    profile.refresh_from_db()

    assert profile.keywords == ["python", "django"]


@pytest.mark.django_db
def test_target_role_profile_requires_keyword_list() -> None:
    """Target role keywords should be stored as a list."""
    profile = TargetRoleProfile(
        owner=UserFactory(),
        title="Backend Engineer",
        keywords="python",
    )

    with pytest.raises(ValidationError, match="Keywords must be stored as a list."):
        profile.save()


@pytest.mark.django_db
def test_target_role_profile_requires_at_least_one_keyword() -> None:
    """Target role profiles should reject empty keyword lists."""
    profile = TargetRoleProfile(
        owner=UserFactory(),
        title="Backend Engineer",
        keywords=[],
    )

    with pytest.raises(ValidationError, match="At least one target keyword"):
        profile.save()


@pytest.mark.django_db
def test_job_insight_has_readable_string_representation() -> None:
    """A job insight should render against its parent application."""
    insight = JobInsightFactory(
        job_application=JobApplicationFactory(
            title="Backend Engineer",
            company="Example Ltd",
        )
    )

    assert str(insight) == "Insight for Backend Engineer at Example Ltd"


@pytest.mark.django_db
def test_job_insight_persists_retrieval_style_output() -> None:
    """Job insights should store explainable retrieval-style output."""
    insight = JobInsightFactory(similarity_score=0.75, score_label="Excellent match")

    insight.refresh_from_db()

    assert insight.similarity_score == 0.75
    assert insight.score_label == "Excellent match"
    assert insight.pipeline_version == "nltk-tfidf-cosine-v1"
    assert insight.extracted_terms
    assert insight.top_overlapping_terms


@pytest.mark.django_db
def test_job_insight_uses_tfidf_pipeline_version() -> None:
    """Job insights should persist the allowed TF-IDF pipeline version."""
    insight = JobInsightFactory()

    insight.refresh_from_db()

    assert insight.pipeline_version == JobInsight.PipelineVersion.NLTK_TFIDF_COSINE_V1


@pytest.mark.django_db
def test_job_insight_rejects_non_tfidf_pipeline_version() -> None:
    """Job insights should reject unsupported non-TF-IDF pipeline versions."""
    owner = UserFactory()
    application = JobApplicationFactory(owner=owner)
    target_profile = TargetRoleProfileFactory(owner=owner)
    insight = JobInsight(
        job_application=application,
        target_profile=target_profile,
        source_hash="c" * 64,
        pipeline_version="embedding-cosine-v1",
        similarity_score=0.5,
        score_label="Partial match",
        explanation="Partial match.",
    )

    with pytest.raises(ValidationError, match="not a valid choice"):
        insight.save()


@pytest.mark.django_db
def test_job_insight_rejects_mismatched_application_and_profile_owner() -> None:
    """A job insight should require the application and profile to share an owner."""
    application = JobApplicationFactory(owner=UserFactory(email="owner@example.com"))
    target_profile = TargetRoleProfileFactory(
        owner=UserFactory(email="other@example.com")
    )
    insight = JobInsight(
        job_application=application,
        target_profile=target_profile,
        source_hash="a" * 64,
        pipeline_version=JobInsight.PipelineVersion.NLTK_TFIDF_COSINE_V1,
        similarity_score=0.5,
        score_label="Partial match",
        explanation="Partial match.",
    )

    with pytest.raises(ValidationError, match="must share an owner"):
        insight.save()


@pytest.mark.django_db
def test_job_insight_requires_json_list_fields() -> None:
    """Stored insight term fields should reject non-list values."""
    owner = UserFactory()
    application = JobApplicationFactory(owner=owner)
    target_profile = TargetRoleProfileFactory(owner=owner)
    insight = JobInsight(
        job_application=application,
        target_profile=target_profile,
        source_hash="b" * 64,
        pipeline_version=JobInsight.PipelineVersion.NLTK_TFIDF_COSINE_V1,
        extracted_terms="python",
        top_overlapping_terms=[],
        missing_target_terms=[],
        similarity_score=0.5,
        score_label="Partial match",
        explanation="Partial match.",
    )

    with pytest.raises(ValidationError, match="This field must be a list."):
        insight.save()
