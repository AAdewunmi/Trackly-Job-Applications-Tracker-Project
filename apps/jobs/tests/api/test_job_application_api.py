"""
API tests for authenticated job application workflow behaviour.
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.jobs.factories import JobApplicationFactory
from apps.jobs.models import JobApplication
from apps.users.factories import UserFactory

pytestmark = pytest.mark.django_db


def create_user(
    email: str = "api.user@example.com",
    password: str = "pass12345",
):
    """Create a user for API tests."""
    return UserFactory(
        email=email,
        password=password,
    )


def authenticated_client(user):
    """Return a DRF API client authenticated as the supplied user."""
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def test_token_obtain_pair_accepts_email_and_password() -> None:
    """JWT token endpoint should issue tokens for valid credentials."""
    password = "safe-test-pass-123"
    create_user(email="token.user@example.com", password=password)

    response = APIClient().post(
        reverse("token_obtain_pair"),
        {"email": "token.user@example.com", "password": password},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data
    assert "refresh" in response.data


def test_authenticated_user_can_list_own_applications() -> None:
    """Application API list should return only the current user's records."""
    user = create_user()
    other_user = create_user(email="other@example.com")
    own_application = JobApplicationFactory(owner=user, title="Backend Engineer")
    JobApplicationFactory(owner=other_user, title="Hidden Role")

    response = authenticated_client(user).get(reverse("job-application-list-create"))

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]["id"] == own_application.id
    assert response.data[0]["title"] == "Backend Engineer"


def test_authenticated_user_can_create_application() -> None:
    """Application API create should persist a user-owned application."""
    user = create_user()
    payload = {
        "title": "Graduate Django Engineer",
        "company": "Trackly Labs",
        "status": JobApplication.Status.APPLIED,
        "job_link": "https://example.com/jobs/1",
        "applied_date": "2026-04-01",
        "job_description": "Python Django REST PostgreSQL Docker testing.",
        "notes": "Applied through careers page.",
    }

    response = authenticated_client(user).post(
        reverse("job-application-list-create"),
        payload,
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    application = JobApplication.objects.get(id=response.data["id"])
    assert application.owner == user
    assert application.title == "Graduate Django Engineer"
    assert application.job_description == payload["job_description"]


def test_authenticated_user_can_retrieve_application_detail() -> None:
    """Application API detail should return the requested owned application."""
    user = create_user()
    application = JobApplicationFactory(owner=user)

    response = authenticated_client(user).get(
        reverse(
            "job-application-detail",
            kwargs={"pk": application.pk},
        )
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == application.pk


def test_authenticated_user_can_update_application() -> None:
    """Application API update should allow the owner to edit application fields."""
    user = create_user()
    application = JobApplicationFactory(owner=user, status=JobApplication.Status.SAVED)

    response = authenticated_client(user).patch(
        reverse(
            "job-application-detail",
            kwargs={"pk": application.pk},
        ),
        {"status": JobApplication.Status.INTERVIEWING},
        format="json",
    )

    application.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert application.status == JobApplication.Status.INTERVIEWING


def test_authenticated_user_can_update_job_description() -> None:
    """Application API update should support job description edits."""
    user = create_user()
    application = JobApplicationFactory(owner=user, job_description="Old text")

    response = authenticated_client(user).patch(
        reverse(
            "job-application-detail",
            kwargs={"pk": application.pk},
        ),
        {"job_description": "Python Django APIs and testing."},
        format="json",
    )

    application.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert "Python Django" in application.job_description


def test_authenticated_user_can_delete_application() -> None:
    """Application API delete should remove an owned application."""
    user = create_user()
    application = JobApplicationFactory(owner=user)

    response = authenticated_client(user).delete(
        reverse(
            "job-application-detail",
            kwargs={"pk": application.pk},
        )
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not JobApplication.objects.filter(pk=application.pk).exists()
