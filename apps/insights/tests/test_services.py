"""Service tests for target-role job insight generation."""

import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError

from apps.insights.factories import JobInsightFactory, TargetRoleProfileFactory
from apps.insights.models import JobInsight, TargetRoleProfile
from apps.insights.services import (
    TargetRoleProfileRequired,
    _clean_text,
    _similarity_score,
    _source_hash,
    can_generate_insight,
    generate_job_insight,
    get_active_target_profile,
)
from apps.jobs.factories import JobApplicationFactory
from apps.users.factories import UserFactory


@pytest.mark.django_db
def test_active_target_profile_returns_latest_active_profile_for_user() -> None:
    """The active profile selector should ignore inactive and foreign profiles."""
    owner = UserFactory(email="owner@example.com")
    other_user = UserFactory(email="other@example.com")
    TargetRoleProfileFactory(owner=owner, title="Inactive", is_active=False)
    TargetRoleProfileFactory(owner=other_user, title="Foreign")
    active_profile = TargetRoleProfileFactory(owner=owner, title="Active")

    assert get_active_target_profile(owner) == active_profile


@pytest.mark.django_db
def test_active_target_profile_returns_none_for_anonymous_user() -> None:
    """Anonymous users should not have an insight baseline."""
    TargetRoleProfileFactory()

    assert get_active_target_profile(AnonymousUser()) is None
    assert can_generate_insight(AnonymousUser()) is False


@pytest.mark.django_db
def test_user_with_active_target_profile_can_generate_insights() -> None:
    """Users with an active baseline should be eligible for insight generation."""
    user = UserFactory()
    TargetRoleProfileFactory(owner=user, is_active=True)

    assert can_generate_insight(user) is True


@pytest.mark.django_db
def test_user_without_target_profile_cannot_generate_insight() -> None:
    """A target role baseline should be required before matching a job."""
    application = JobApplicationFactory()

    with pytest.raises(
        TargetRoleProfileRequired,
        match="active target role profile is required",
    ):
        generate_job_insight(application)


@pytest.mark.django_db
def test_user_with_active_target_profile_can_generate_insight() -> None:
    """A user with a target baseline should receive a stored job insight."""
    owner = UserFactory(email="owner@example.com")
    application = JobApplicationFactory(
        owner=owner,
        title="Backend Engineer",
        company="Example Ltd",
        job_description="Build Python Django APIs with PostgreSQL and tests.",
    )
    target_profile = TargetRoleProfileFactory(
        owner=owner,
        title="Backend Engineer",
        keywords=["python", "django", "api", "postgresql"],
    )

    insight = generate_job_insight(application)

    assert insight.job_application == application
    assert insight.target_profile == target_profile
    assert insight.pipeline_version == JobInsight.PipelineVersion.NLTK_TFIDF_COSINE_V1
    assert insight.similarity_score > 0
    assert insight.score_label in {"Partial match", "Strong match"}
    assert JobInsight.objects.filter(job_application=application).count() == 1


@pytest.mark.django_db
def test_generate_insight_stores_cleaned_text_terms_and_explanation() -> None:
    """Generated insights should persist explainable matching output."""
    owner = UserFactory(email="owner@example.com")
    application = JobApplicationFactory(
        owner=owner,
        title="Backend Backend Engineer",
        company="Example Ltd",
        job_description=(
            "Build Python, Django, and API services. Testing APIs with Python."
        ),
        notes="PostgreSQL experience preferred.",
    )
    target_profile = TargetRoleProfileFactory(
        owner=owner,
        title="Backend Engineer",
        description="Python Django API delivery.",
        keywords=["python", "django", "api", "postgresql", "testing"],
    )

    insight = generate_job_insight(application, target_profile)

    assert insight.clean_job_text == (
        "backend backend engineer example ltd build python django and api "
        "services testing apis with python postgresql experience preferred"
    )
    assert insight.clean_target_text == (
        "backend engineer python django api delivery python django api "
        "postgresql testing"
    )
    assert insight.extracted_terms == [
        "backend",
        "engineer",
        "example",
        "ltd",
        "build",
        "python",
        "django",
        "and",
        "api",
        "services",
        "testing",
        "apis",
        "with",
        "postgresql",
        "experience",
        "preferred",
    ]
    assert insight.top_overlapping_terms == [
        "backend",
        "engineer",
        "python",
        "django",
        "api",
        "postgresql",
        "testing",
    ]
    assert insight.missing_target_terms == ["delivery"]
    assert "overlaps with your target profile on backend" in insight.explanation
    assert "Missing or weaker target terms include delivery" in insight.explanation


@pytest.mark.django_db
def test_generate_insight_labels_jobs_with_no_overlap_as_low_match() -> None:
    """A job with no target keyword overlap should be labelled as low match."""
    owner = UserFactory(email="owner@example.com")
    application = JobApplicationFactory(
        owner=owner,
        title="Customer Success Associate",
        company="Example Ltd",
        job_description="Handle account renewals and customer onboarding.",
        notes="Remote role with stakeholder communication.",
    )
    TargetRoleProfileFactory(
        owner=owner,
        title="Backend Engineer",
        description="Server-side platform work.",
        keywords=["python", "django", "postgresql"],
    )

    insight = generate_job_insight(application)

    assert insight.similarity_score == 0
    assert insight.score_label == "Low match"
    assert insight.top_overlapping_terms == []
    assert insight.missing_target_terms == [
        "backend",
        "engineer",
        "server",
        "side",
        "platform",
        "work",
        "python",
        "django",
        "postgresql",
    ]


@pytest.mark.django_db
def test_generate_insight_rejects_foreign_target_profile() -> None:
    """A user should not match a job against another user's baseline."""
    application = JobApplicationFactory(owner=UserFactory(email="owner@example.com"))
    foreign_profile = TargetRoleProfileFactory(
        owner=UserFactory(email="other@example.com")
    )

    with pytest.raises(ValidationError, match="must share an owner"):
        generate_job_insight(application, target_profile=foreign_profile)


@pytest.mark.django_db
def test_generate_insight_rejects_inactive_target_profile() -> None:
    """Inactive baselines should not be used for job matching."""
    owner = UserFactory(email="owner@example.com")
    application = JobApplicationFactory(owner=owner)
    inactive_profile = TargetRoleProfileFactory(owner=owner, is_active=False)

    with pytest.raises(
        TargetRoleProfileRequired,
        match="active target role profile is required",
    ):
        generate_job_insight(application, target_profile=inactive_profile)


@pytest.mark.django_db
def test_generate_insight_updates_existing_unchanged_source() -> None:
    """Generating the same insight twice should not duplicate unchanged output."""
    owner = UserFactory(email="owner@example.com")
    application = JobApplicationFactory(owner=owner)
    target_profile = TargetRoleProfileFactory(owner=owner)

    first_insight = generate_job_insight(application, target_profile)
    second_insight = generate_job_insight(application, target_profile)

    assert second_insight == first_insight
    assert JobInsight.objects.count() == 1


@pytest.mark.django_db
def test_generate_insight_creates_new_record_when_source_text_changes() -> None:
    """Changed source text should produce a new insight source hash."""
    owner = UserFactory(email="owner@example.com")
    application = JobApplicationFactory(
        owner=owner,
        job_description="Build Python APIs.",
    )
    target_profile = TargetRoleProfileFactory(
        owner=owner,
        keywords=["python", "django", "api"],
    )

    first_insight = generate_job_insight(application, target_profile)
    application.job_description = "Build Python and Django APIs."
    application.save()
    second_insight = generate_job_insight(application, target_profile)

    assert second_insight != first_insight
    assert second_insight.source_hash != first_insight.source_hash
    assert JobInsight.objects.count() == 2


def test_clean_text_normalises_values_for_matching() -> None:
    """Text cleaning should produce deterministic lowercase token text."""
    assert (
        _clean_text("Python/Django APIs.", None, "C++ and C# roles")
        == "python django apis none c++ and c# roles"
    )


def test_source_hash_includes_cleaned_text_and_pipeline_version() -> None:
    """The hash should change when either cleaned input changes."""
    original_hash = _source_hash("python django", "python")

    assert _source_hash("python django", "python") == original_hash
    assert _source_hash("python django api", "python") != original_hash
    assert _source_hash("python django", "python api") != original_hash


def test_similarity_score_returns_zero_without_target_terms() -> None:
    """The defensive score helper should handle missing target terms."""
    assert _similarity_score(["python"], []) == 0.0


@pytest.mark.django_db
def test_target_role_profile_requires_keywords() -> None:
    """A target baseline should need meaningful matching keywords."""
    profile = TargetRoleProfile(
        owner=UserFactory(),
        title="Backend Engineer",
        keywords=[" ", ""],
    )

    with pytest.raises(ValidationError, match="At least one target keyword"):
        profile.save()


@pytest.mark.django_db
def test_job_insight_factory_uses_same_owner_for_application_and_profile() -> None:
    """The insight factory should build records that respect ownership rules."""
    insight = JobInsightFactory()

    assert insight.job_application.owner == insight.target_profile.owner
