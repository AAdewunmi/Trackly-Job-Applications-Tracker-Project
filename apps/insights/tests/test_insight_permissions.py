"""
Integration tests for browser-based insight generation permissions.
"""

import pytest
from django.urls import reverse

from apps.insights.factories import TargetRoleProfileFactory
from apps.insights.models import JobInsight
from apps.jobs.factories import JobApplicationFactory
from apps.users.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_logged_in_user_can_generate_insight_from_application_detail(client) -> None:
    """A user should generate an insight for their own application."""
    user = UserFactory()
    application = JobApplicationFactory(
        owner=user,
        job_description="Python Django PostgreSQL Docker testing",
    )
    profile = TargetRoleProfileFactory(
        owner=user,
        keywords=["python", "django", "docker"],
    )
    client.force_login(user)

    response = client.post(
        reverse(
            "insights:job-insight-generate",
            kwargs={"application_pk": application.pk},
        ),
        {"target_profile": profile.pk},
    )

    assert response.status_code == 302
    assert response.url == reverse(
        "jobs:application_detail",
        kwargs={"pk": application.pk},
    )
    assert JobInsight.objects.filter(job_application=application).exists()


def test_user_cannot_generate_insight_for_another_users_application(client) -> None:
    """Cross-user application insight generation should return 404."""
    user = UserFactory()
    owner = UserFactory(email="owner.ui@example.com")
    application = JobApplicationFactory(owner=owner)
    profile = TargetRoleProfileFactory(owner=user)
    client.force_login(user)

    response = client.post(
        reverse(
            "insights:job-insight-generate",
            kwargs={"application_pk": application.pk},
        ),
        {"target_profile": profile.pk},
    )

    assert response.status_code == 404
    assert JobInsight.objects.count() == 0


def test_user_cannot_use_another_users_target_profile(client) -> None:
    """Cross-user target profile selection should not create an insight."""
    user = UserFactory()
    other_user = UserFactory(email="profile.owner@example.com")
    application = JobApplicationFactory(owner=user)
    profile = TargetRoleProfileFactory(owner=other_user)
    client.force_login(user)

    response = client.post(
        reverse(
            "insights:job-insight-generate",
            kwargs={"application_pk": application.pk},
        ),
        {"target_profile": profile.pk},
    )

    assert response.status_code == 302
    assert JobInsight.objects.count() == 0


def test_anonymous_user_is_redirected_from_insight_generation(client) -> None:
    """Anonymous browser requests should be redirected to login."""
    application = JobApplicationFactory()

    response = client.post(
        reverse(
            "insights:job-insight-generate",
            kwargs={"application_pk": application.pk},
        )
    )

    assert response.status_code == 302
    assert "/accounts/login/" in response.url
