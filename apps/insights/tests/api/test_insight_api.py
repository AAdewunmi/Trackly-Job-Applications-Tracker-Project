"""
API tests for secured Trackly insight generation.
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.insights.factories import JobInsightFactory, TargetRoleProfileFactory
from apps.insights.models import JobInsight
from apps.jobs.factories import JobApplicationFactory
from apps.users.factories import UserFactory


pytestmark = pytest.mark.django_db


def authenticated_client(user):
    """Return an authenticated DRF API client."""
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def test_unauthenticated_user_cannot_list_insights() -> None:
    """Anonymous users should not read insight API output."""
    response = APIClient().get(reverse("insights_api:job-insight-list"))

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_authenticated_user_can_generate_insight() -> None:
    """Authenticated users should generate insights for their own data."""
    user = UserFactory()
    application = JobApplicationFactory(
        owner=user,
        job_description="Python Django REST API PostgreSQL Docker",
    )
    profile = TargetRoleProfileFactory(
        owner=user,
        keywords=["python", "django", "postgresql"],
    )

    response = authenticated_client(user).post(
        reverse("insights_api:job-insight-generate"),
        {
            "job_application_id": application.pk,
            "target_profile_id": profile.pk,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["created"] is True
    assert response.data["insight"]["job_application"] == application.pk
    assert response.data["insight"]["top_overlapping_terms"]
    assert JobInsight.objects.filter(job_application=application).exists()


def test_api_insight_generation_is_idempotent_for_unchanged_content() -> None:
    """Repeated API generation should reuse unchanged insights."""
    user = UserFactory()
    application = JobApplicationFactory(
        owner=user,
        job_description="Python Django testing",
    )
    profile = TargetRoleProfileFactory(owner=user, keywords=["python", "django"])
    client = authenticated_client(user)
    payload = {
        "job_application_id": application.pk,
        "target_profile_id": profile.pk,
    }

    first = client.post(
        reverse("insights_api:job-insight-generate"),
        payload,
        format="json",
    )
    second = client.post(
        reverse("insights_api:job-insight-generate"),
        payload,
        format="json",
    )

    assert first.status_code == status.HTTP_201_CREATED
    assert second.status_code == status.HTTP_200_OK
    assert second.data["created"] is False
    assert JobInsight.objects.count() == 1


def test_authenticated_user_can_list_own_insights() -> None:
    """Insight list API should return current user's insights."""
    user = UserFactory()
    other_user = UserFactory(email="api.other.insight@example.com")
    own_insight = JobInsightFactory(job_application__owner=user)
    JobInsightFactory(job_application__owner=other_user)

    response = authenticated_client(user).get(reverse("insights_api:job-insight-list"))

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]["id"] == own_insight.pk


def test_user_cannot_generate_insight_for_another_users_application() -> None:
    """Insight API should hide applications owned by another user."""
    user = UserFactory()
    owner = UserFactory(email="api.owner.application@example.com")
    application = JobApplicationFactory(owner=owner)
    profile = TargetRoleProfileFactory(owner=user)

    response = authenticated_client(user).post(
        reverse("insights_api:job-insight-generate"),
        {
            "job_application_id": application.pk,
            "target_profile_id": profile.pk,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_user_cannot_use_another_users_target_profile() -> None:
    """Insight API should hide target profiles owned by another user."""
    user = UserFactory()
    owner = UserFactory(email="api.owner.profile@example.com")
    application = JobApplicationFactory(owner=user)
    profile = TargetRoleProfileFactory(owner=owner)

    response = authenticated_client(user).post(
        reverse("insights_api:job-insight-generate"),
        {
            "job_application_id": application.pk,
            "target_profile_id": profile.pk,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
