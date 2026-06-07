"""
API permission tests for Trackly job application endpoints.
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.jobs.factories import JobApplicationFactory
from apps.jobs.models import JobApplication
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


def test_unauthenticated_user_cannot_retrieve_application() -> None:
    """Anonymous API detail requests should be rejected."""
    application = JobApplicationFactory()

    response = APIClient().get(
        reverse("job-application-detail", kwargs={"pk": application.pk})
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_unauthenticated_user_cannot_update_application() -> None:
    """Anonymous API update requests should be rejected."""
    application = JobApplicationFactory(title="Original")

    response = APIClient().patch(
        reverse("job-application-detail", kwargs={"pk": application.pk}),
        {"title": "Changed"},
        format="json",
    )

    application.refresh_from_db()
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert application.title == "Original"


def test_unauthenticated_user_cannot_delete_application() -> None:
    """Anonymous API delete requests should be rejected."""
    application = JobApplicationFactory()

    response = APIClient().delete(
        reverse("job-application-detail", kwargs={"pk": application.pk})
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert JobApplication.objects.filter(pk=application.pk).exists()


def test_authenticated_user_list_excludes_other_users_applications() -> None:
    """API list ownership should match the browser application list boundary."""
    user = create_user("list.owner@example.com")
    other_user = create_user("list.other@example.com")
    own_application = JobApplicationFactory(owner=user, title="Visible Role")
    hidden_application = JobApplicationFactory(owner=other_user, title="Hidden Role")

    response = authenticated_client(user).get(reverse("job-application-list-create"))

    assert response.status_code == status.HTTP_200_OK
    returned_ids = {application["id"] for application in response.data}
    assert own_application.id in returned_ids
    assert hidden_application.id not in returned_ids


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
    application = JobApplicationFactory(owner=owner, title="Original")

    response = authenticated_client(other_user).patch(
        reverse(
            "job-application-detail",
            kwargs={"pk": application.pk},
        ),
        {"title": "Changed"},
        format="json",
    )

    application.refresh_from_db()
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert application.title == "Original"


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
    assert JobApplication.objects.filter(pk=application.pk).exists()
