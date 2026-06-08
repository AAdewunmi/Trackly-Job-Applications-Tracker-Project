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
        pipeline_version="keyword-overlap-v1",
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
        pipeline_version="keyword-overlap-v1",
        extracted_terms="python",
        top_overlapping_terms=[],
        missing_target_terms=[],
        similarity_score=0.5,
        score_label="Partial match",
        explanation="Partial match.",
    )

    with pytest.raises(ValidationError, match="This field must be a list."):
        insight.save()
