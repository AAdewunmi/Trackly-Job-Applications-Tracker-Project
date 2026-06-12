"""Selector tests for user-scoped insight queries."""

from datetime import timedelta

import pytest
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone

from apps.insights.factories import JobInsightFactory, TargetRoleProfileFactory
from apps.insights.selectors import (
    get_active_target_profiles_for_user,
    get_filtered_insights_for_user,
    get_insights_for_user,
    get_latest_insight_for_application,
    get_recent_insights_for_user,
    get_score_labels_for_user,
    get_target_profiles_for_user,
)
from apps.jobs.factories import JobApplicationFactory
from apps.users.factories import UserFactory


def set_insight_created_at(insight, created_at) -> None:
    """Set an insight timestamp after factory save hooks run."""
    type(insight).objects.filter(pk=insight.pk).update(created_at=created_at)
    insight.refresh_from_db()


@pytest.mark.django_db
def test_target_profiles_for_user_returns_owned_profiles_in_display_order() -> None:
    """Profile selectors should be scoped to owner and order active profiles first."""
    owner = UserFactory(email="owner@example.com")
    other_user = UserFactory(email="other@example.com")
    inactive_profile = TargetRoleProfileFactory(
        owner=owner,
        title="Z Inactive",
        is_active=False,
    )
    active_profile = TargetRoleProfileFactory(
        owner=owner,
        title="A Active",
        is_active=True,
    )
    TargetRoleProfileFactory(owner=other_user, title="Foreign")

    profiles = get_target_profiles_for_user(owner)

    assert list(profiles) == [active_profile, inactive_profile]


@pytest.mark.django_db
def test_target_profile_selectors_return_empty_for_anonymous_user() -> None:
    """Anonymous users should not receive target profiles."""
    TargetRoleProfileFactory()

    assert list(get_target_profiles_for_user(AnonymousUser())) == []
    assert list(get_active_target_profiles_for_user(AnonymousUser())) == []


@pytest.mark.django_db
def test_target_profile_selectors_return_empty_for_unsaved_user(
    django_user_model,
) -> None:
    """Unsaved user-like objects should not leak target profiles."""
    TargetRoleProfileFactory()
    unsaved_user = django_user_model()

    assert get_target_profiles_for_user(unsaved_user).count() == 0
    assert get_active_target_profiles_for_user(unsaved_user).count() == 0


@pytest.mark.django_db
def test_active_target_profiles_for_user_returns_only_active_profiles() -> None:
    """Active profile selector should exclude inactive and foreign profiles."""
    owner = UserFactory(email="owner@example.com")
    other_user = UserFactory(email="other@example.com")
    active_profile = TargetRoleProfileFactory(owner=owner, title="Backend")
    TargetRoleProfileFactory(owner=owner, title="Inactive", is_active=False)
    TargetRoleProfileFactory(owner=other_user, title="Foreign")

    profiles = get_active_target_profiles_for_user(owner)

    assert list(profiles) == [active_profile]


@pytest.mark.django_db
def test_latest_insight_for_application_returns_most_recent_application_insight() -> (
    None
):
    """Application insight lookup should use JobInsight model ordering."""
    application = JobApplicationFactory()
    first_insight = JobInsightFactory(job_application=application)
    second_insight = JobInsightFactory(job_application=application)
    now = timezone.now()
    set_insight_created_at(first_insight, now - timedelta(days=1))
    set_insight_created_at(second_insight, now)

    assert get_latest_insight_for_application(application) == second_insight


@pytest.mark.django_db
def test_insights_for_user_returns_owned_insights_in_recent_order() -> None:
    """Insight selectors should be scoped through application ownership."""
    owner = UserFactory(email="owner@example.com")
    other_user = UserFactory(email="other@example.com")
    first_insight = JobInsightFactory(job_application__owner=owner)
    second_insight = JobInsightFactory(job_application__owner=owner)
    JobInsightFactory(job_application__owner=other_user)
    now = timezone.now()
    set_insight_created_at(first_insight, now - timedelta(days=1))
    set_insight_created_at(second_insight, now)

    insights = get_insights_for_user(owner)

    assert list(insights) == [second_insight, first_insight]


@pytest.mark.django_db
def test_filtered_insights_for_user_filters_by_profile_and_score_label() -> None:
    """Insight filtering should stay scoped to the current user's records."""
    owner = UserFactory(email="owner@example.com")
    backend_profile = TargetRoleProfileFactory(owner=owner, title="Backend")
    data_profile = TargetRoleProfileFactory(owner=owner, title="Data")
    backend_insight = JobInsightFactory(
        job_application__owner=owner,
        target_profile=backend_profile,
        score_label="Strong match",
    )
    JobInsightFactory(
        job_application__owner=owner,
        target_profile=data_profile,
        score_label="Developing match",
    )
    JobInsightFactory(score_label="Strong match")

    insights = get_filtered_insights_for_user(
        owner,
        target_profile_id=str(backend_profile.pk),
        score_label="Strong match",
    )

    assert list(insights) == [backend_insight]


@pytest.mark.django_db
def test_filtered_insights_for_user_sorts_by_similarity_score() -> None:
    """Insight sorting should support match strength ordering."""
    owner = UserFactory()
    lower_score = JobInsightFactory(
        job_application__owner=owner,
        similarity_score=0.24,
    )
    higher_score = JobInsightFactory(
        job_application__owner=owner,
        similarity_score=0.91,
    )

    insights = get_filtered_insights_for_user(owner, sort="score_desc")

    assert list(insights) == [higher_score, lower_score]


@pytest.mark.django_db
def test_score_labels_for_user_returns_owned_distinct_labels() -> None:
    """Score label options should be deduplicated and user scoped."""
    owner = UserFactory()
    JobInsightFactory(job_application__owner=owner, score_label="Strong match")
    JobInsightFactory(job_application__owner=owner, score_label="Strong match")
    JobInsightFactory(job_application__owner=owner, score_label="Developing match")
    JobInsightFactory(score_label="Foreign")

    assert get_score_labels_for_user(owner) == [
        "Developing match",
        "Strong match",
    ]


@pytest.mark.django_db
def test_insight_selectors_return_empty_for_anonymous_user() -> None:
    """Anonymous users should not receive stored insights."""
    JobInsightFactory()

    assert list(get_insights_for_user(AnonymousUser())) == []
    assert list(get_filtered_insights_for_user(AnonymousUser())) == []
    assert get_score_labels_for_user(AnonymousUser()) == []
    assert get_recent_insights_for_user(AnonymousUser()) == []


@pytest.mark.django_db
def test_recent_insights_for_user_respects_limit() -> None:
    """Recent insight selector should return a bounded list."""
    owner = UserFactory()
    first_insight = JobInsightFactory(job_application__owner=owner)
    second_insight = JobInsightFactory(job_application__owner=owner)
    third_insight = JobInsightFactory(job_application__owner=owner)
    now = timezone.now()
    set_insight_created_at(first_insight, now - timedelta(days=2))
    set_insight_created_at(second_insight, now - timedelta(days=1))
    set_insight_created_at(third_insight, now)

    insights = get_recent_insights_for_user(owner, limit=2)

    assert insights == [third_insight, second_insight]
