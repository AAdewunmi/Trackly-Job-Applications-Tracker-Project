"""
Service tests for retrieval-style job insight generation.
"""

import pytest
from django.core.exceptions import PermissionDenied

from apps.insights.factories import TargetRoleProfileFactory
from apps.insights.models import JobInsight
from apps.insights.nlp.similarity import PIPELINE_VERSION
from apps.insights.services import (
    build_job_source_text,
    build_target_source_text,
    calculate_source_hash,
    generate_job_insight,
)
from apps.jobs.factories import JobApplicationFactory
from apps.users.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_build_job_source_text_combines_application_fields() -> None:
    """Source text should include title, company, description, and notes."""
    application = JobApplicationFactory(
        title="Backend Engineer",
        company="Example Ltd",
        job_description="Python Django APIs",
        notes="Remote role",
    )

    source_text = build_job_source_text(application)

    assert "Backend Engineer" in source_text
    assert "Example Ltd" in source_text
    assert "Python Django APIs" in source_text
    assert "Remote role" in source_text


def test_build_target_source_text_combines_target_profile_fields() -> None:
    """Target source text should include title, description, and keywords."""
    profile = TargetRoleProfileFactory(
        title="Graduate Backend Engineer",
        description="Python Django APIs",
        keywords=["postgresql", "docker"],
    )

    source_text = build_target_source_text(profile)

    assert "Graduate Backend Engineer" in source_text
    assert "Python Django APIs" in source_text
    assert "postgresql" in source_text
    assert "docker" in source_text


def test_calculate_source_hash_is_stable() -> None:
    """Source hashing should be deterministic for the same source input."""
    first = calculate_source_hash(
        job_source_text="Python Django",
        target_source_text="Django Python",
    )
    second = calculate_source_hash(
        job_source_text="Python Django",
        target_source_text="Django Python",
    )

    assert first == second
    assert len(first) == 64


def test_generate_job_insight_persists_retrieval_style_output() -> None:
    """Insight generation should persist structured TF-IDF similarity output."""
    user = UserFactory()
    application = JobApplicationFactory(
        owner=user,
        job_description="Python Django REST API testing Docker",
    )
    profile = TargetRoleProfileFactory(
        owner=user,
        keywords=["python", "django", "docker", "postgresql"],
    )

    result = generate_job_insight(
        user=user,
        application=application,
        target_profile=profile,
    )

    assert result.created is True
    assert JobInsight.objects.count() == 1
    assert result.insight.job_application == application
    assert result.insight.target_profile == profile
    assert result.insight.pipeline_version == PIPELINE_VERSION
    assert result.insight.similarity_score > 0
    assert "postgresql" in result.insight.missing_target_terms


def test_generate_job_insight_is_idempotent_for_unchanged_content() -> None:
    """Repeated generation for unchanged source text should reuse the insight."""
    user = UserFactory()
    application = JobApplicationFactory(
        owner=user,
        job_description="Python Django PostgreSQL",
    )
    profile = TargetRoleProfileFactory(
        owner=user,
        keywords=["python", "django", "postgresql"],
    )

    first = generate_job_insight(
        user=user,
        application=application,
        target_profile=profile,
    )
    second = generate_job_insight(
        user=user,
        application=application,
        target_profile=profile,
    )

    assert first.created is True
    assert second.created is False
    assert first.insight.pk == second.insight.pk
    assert JobInsight.objects.count() == 1


def test_generate_job_insight_creates_new_record_when_source_changes() -> None:
    """Changed job source text should produce a new hash and new insight."""
    user = UserFactory()
    application = JobApplicationFactory(
        owner=user,
        job_description="Python Django",
    )
    profile = TargetRoleProfileFactory(owner=user, keywords=["python", "django"])

    first = generate_job_insight(
        user=user,
        application=application,
        target_profile=profile,
    )
    application.job_description = "Python Django Docker"
    application.save()
    second = generate_job_insight(
        user=user,
        application=application,
        target_profile=profile,
    )

    assert first.insight.pk != second.insight.pk
    assert JobInsight.objects.count() == 2


def test_generate_job_insight_rejects_cross_user_application() -> None:
    """Users should not generate insights for another user's application."""
    user = UserFactory()
    owner = UserFactory(email="owner.generation@example.com")
    application = JobApplicationFactory(owner=owner)
    profile = TargetRoleProfileFactory(owner=user)

    with pytest.raises(PermissionDenied):
        generate_job_insight(
            user=user,
            application=application,
            target_profile=profile,
        )
