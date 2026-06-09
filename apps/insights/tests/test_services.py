"""Service tests for target-role job insight generation."""

import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError

from apps.insights import services
from apps.insights.factories import JobInsightFactory, TargetRoleProfileFactory
from apps.insights.models import JobInsight, TargetRoleProfile
from apps.insights.nlp.similarity import TextSimilarityResult, score_label_for
from apps.insights.services import (
    TargetRoleProfileRequired,
    _clean_text,
    _source_hash,
    build_job_source_text,
    build_target_source_text,
    calculate_source_hash,
    can_generate_insight,
    generate_job_insight,
    get_active_target_profile,
)
from apps.jobs.factories import JobApplicationFactory
from apps.users.factories import UserFactory

LOW_VALUE_TERMS = {"and", "about", "target", "role", "using"}


def assert_low_value_terms_excluded(terms: list[str]) -> None:
    """Assert that low-value terms do not appear as terms or n-gram parts."""
    for term in terms:
        assert term not in LOW_VALUE_TERMS
        assert LOW_VALUE_TERMS.isdisjoint(term.split())


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
def test_build_job_source_text_joins_non_empty_application_fields() -> None:
    """The job-side source text should preserve meaningful application fields."""
    application = JobApplicationFactory(
        title="Backend Engineer",
        company="Example Ltd",
        job_description="Build Django APIs.",
        notes="",
    )

    assert build_job_source_text(application) == (
        "Backend Engineer\nExample Ltd\nBuild Django APIs."
    )


@pytest.mark.django_db
def test_build_target_source_text_joins_profile_fields_and_keywords() -> None:
    """The target-side source text should include profile keywords."""
    target_profile = TargetRoleProfileFactory(
        title="Backend Engineer",
        description="Server-side product work.",
        keywords=["python", "django", "postgresql"],
    )

    assert build_target_source_text(target_profile) == (
        "Backend Engineer\nServer-side product work.\npython django postgresql"
    )


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
    assert insight.score_label in {"Partial match", "Strong match", "Excellent match"}
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

    clean_job_terms = insight.clean_job_text.split()
    clean_target_terms = insight.clean_target_text.split()

    assert clean_job_terms[:10] == [
        "backend",
        "backend",
        "engineer",
        "example",
        "ltd",
        "build",
        "python",
        "django",
        "api",
        "service",
    ]
    assert "and" not in clean_job_terms
    assert "with" not in clean_job_terms
    assert "services" not in clean_job_terms
    assert "testing" not in clean_job_terms
    assert "test" in clean_job_terms
    assert "postgresql" in clean_job_terms
    assert {"prefer", "preferr"} & set(clean_job_terms)
    assert clean_target_terms == [
        "backend",
        "engineer",
        "python",
        "django",
        "api",
        "delivery",
        "python",
        "django",
        "api",
        "postgresql",
        "test",
    ]
    assert insight.extracted_terms
    assert len(insight.extracted_terms) <= 12
    assert "backend" in insight.extracted_terms
    assert "python" in insight.extracted_terms
    assert {"api", "apis"} & set(insight.extracted_terms)
    assert insight.similarity_score > 0
    assert insight.score_label == "Partial match"
    assert "python" in insight.top_overlapping_terms
    assert "backend" in insight.top_overlapping_terms
    assert "django api" in insight.top_overlapping_terms
    assert "delivery" in insight.missing_target_terms
    assert "api delivery" in insight.missing_target_terms
    assert "overlaps with your target profile on" in insight.explanation
    assert "Missing or weaker target terms include" in insight.explanation


@pytest.mark.django_db
def test_generate_insight_excludes_low_value_terms_from_evidence() -> None:
    """Generated insight evidence should exclude configured low-value terms."""
    owner = UserFactory(email="owner@example.com")
    application = JobApplicationFactory(
        owner=owner,
        title="Target Backend Role",
        company="Example Ltd",
        job_description="Using Python and Django about API delivery.",
    )
    target_profile = TargetRoleProfileFactory(
        owner=owner,
        title="Target Backend Role",
        description="Using Python Django about PostgreSQL.",
        keywords=["target", "role", "using", "python", "django", "postgresql"],
    )

    insight = generate_job_insight(application, target_profile)

    assert "python" in insight.top_overlapping_terms
    assert "postgresql" in insight.missing_target_terms
    assert "python" in insight.clean_job_text.split()
    assert_low_value_terms_excluded(insight.extracted_terms)
    assert_low_value_terms_excluded(insight.top_overlapping_terms)
    assert_low_value_terms_excluded(insight.missing_target_terms)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("similarity_score", "expected_label"),
    [
        (0.5, "Strong match"),
        (0.25, "Partial match"),
        (0.24, "Low match"),
    ],
)
def test_generate_insight_persists_threshold_score_labels(
    monkeypatch,
    similarity_score: float,
    expected_label: str,
) -> None:
    """Generated insights should persist deterministic threshold labels."""
    owner = UserFactory(email="owner@example.com")
    application = JobApplicationFactory(
        owner=owner,
        title="Backend Engineer",
        job_description="Build Python Django APIs.",
    )
    target_profile = TargetRoleProfileFactory(
        owner=owner,
        title="Backend Engineer",
        keywords=["python", "django", "api"],
    )

    def fake_analyse_text_similarity(
        *,
        job_text: str,
        target_text: str,
    ) -> TextSimilarityResult:
        return TextSimilarityResult(
            clean_job_text=f"job {similarity_score}",
            clean_target_text=f"target {similarity_score}",
            extracted_terms=["python"],
            top_overlapping_terms=["python"],
            missing_target_terms=[],
            similarity_score=similarity_score,
            score_label=score_label_for(similarity_score),
            explanation=f"{expected_label}: deterministic threshold test.",
        )

    monkeypatch.setattr(
        services,
        "analyse_text_similarity",
        fake_analyse_text_similarity,
    )

    insight = generate_job_insight(application, target_profile)

    assert insight.pipeline_version == JobInsight.PipelineVersion.NLTK_TFIDF_COSINE_V1
    assert insight.similarity_score == similarity_score
    assert insight.score_label == expected_label
    assert insight.explanation.startswith(expected_label)


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
    assert "backend" in insight.missing_target_terms
    assert "backend engineer" in insight.missing_target_terms
    assert "platform" in insight.missing_target_terms
    assert "django" in insight.missing_target_terms


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


def test_clean_text_uses_nltk_preprocessing_for_matching() -> None:
    """Text cleaning should use NLTK-backed preprocessing."""
    clean_text = _clean_text("Python/Django APIs.", None, "C++ and C# roles")

    assert clean_text.split() in [
        ["pythondjango", "api", "c++"],
        ["pythondjango", "apis", "c++"],
    ]


def test_source_hash_includes_cleaned_text_and_pipeline_version() -> None:
    """The hash should change when either cleaned input changes."""
    original_hash = _source_hash("python django", "python")

    assert _source_hash("python django", "python") == original_hash
    assert (
        calculate_source_hash(
            clean_job_text="python django",
            clean_target_text="python",
        )
        == original_hash
    )
    assert _source_hash("python django api", "python") != original_hash
    assert _source_hash("python django", "python api") != original_hash
    assert (
        calculate_source_hash(
            clean_job_text="python django",
            clean_target_text="python",
            pipeline_version="other-pipeline",
        )
        != original_hash
    )


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
