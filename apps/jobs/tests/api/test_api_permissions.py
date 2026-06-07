"""
API permission tests for Trackly job application endpoints.
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.jobs.factories import JobApplicationFactory
from apps.users.factories import UserFactory

pytestmark = pytest.mark.django_db


def create_user(email: str):
    """Create a user for API permission tests."""
    return UserFactory(
        email=email,
        password="pass12345",
    )


def authenticated_client(user):
    """Return an API client authenticated as the supplied user."""
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def test_unauthenticated_user_cannot_list_applications() -> None:
    """Anonymous API requests should be rejected."""
    response = APIClient().get(reverse("job-application-list-create"))

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_unauthenticated_user_cannot_create_application() -> None:
    """Anonymous API create requests should be rejected."""
    response = APIClient().post(
        reverse("job-application-list-create"),
        {"title": "Role", "company": "Company"},
        format="json",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_user_cannot_retrieve_another_users_application() -> None:
    """Object ownership should be enforced on retrieve."""
    owner = create_user("owner@example.com")
    other_user = create_user("other@example.com")
    application = JobApplicationFactory(owner=owner)

    response = authenticated_client(other_user).get(
        reverse(
            "job-application-detail",
            kwargs={"pk": application.pk},
        )
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_user_cannot_update_another_users_application() -> None:
    """Object ownership should be enforced on update."""
    owner = create_user("owner.update@example.com")
    other_user = create_user("other.update@example.com")
    application = JobApplicationFactory(owner=owner)

    response = authenticated_client(other_user).patch(
        reverse(
            "job-application-detail",
            kwargs={"pk": application.pk},
        ),
        {"title": "Changed"},
        format="json",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_user_cannot_delete_another_users_application() -> None:
    """Object ownership should be enforced on delete."""
    owner = create_user("owner.delete@example.com")
    other_user = create_user("other.delete@example.com")
    application = JobApplicationFactory(owner=owner)

    response = authenticated_client(other_user).delete(
        reverse(
            "job-application-detail",
            kwargs={"pk": application.pk},
        )
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
