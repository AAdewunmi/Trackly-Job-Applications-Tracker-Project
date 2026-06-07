"""API tests for job application endpoints."""

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.jobs.factories import JobApplicationFactory
from apps.jobs.models import JobApplication
from apps.users.factories import UserFactory


def valid_application_payload(**overrides: object) -> dict[str, object]:
    """Return a valid API payload for a job application."""
    payload = {
        "title": "Backend Engineer",
        "company": "Example Ltd",
        "status": JobApplication.Status.APPLIED,
        "job_link": "https://example.com/jobs/backend-engineer",
        "applied_date": timezone.localdate().isoformat(),
        "job_description": "Build Django services and maintain APIs.",
        "notes": "Applied through the company careers page.",
    }
    payload.update(overrides)
    return payload


@pytest.fixture
def api_client() -> APIClient:
    """Return a DRF API client."""
    return APIClient()


@pytest.mark.django_db
def test_application_api_rejects_unauthenticated_requests(api_client) -> None:
    """Anonymous API requests should be rejected by default permissions."""
    response = api_client.get(reverse("job-application-list-create"))

    assert response.status_code == 401


@pytest.mark.django_db
def test_application_api_lists_only_authenticated_users_records(api_client) -> None:
    """The list endpoint should not expose another user's applications."""
    user = UserFactory()
    other_user = UserFactory()
    own_application = JobApplicationFactory(owner=user, title="Own Role")
    JobApplicationFactory(owner=other_user, title="Other Role")
    api_client.force_authenticate(user=user)

    response = api_client.get(reverse("job-application-list-create"))

    assert response.status_code == 200
    titles = [application["title"] for application in response.data]
    assert titles == [own_application.title]


@pytest.mark.django_db
def test_application_api_create_assigns_owner_from_request_user(api_client) -> None:
    """The create endpoint should ignore posted ownership and use request.user."""
    user = UserFactory()
    other_user = UserFactory()
    api_client.force_authenticate(user=user)

    response = api_client.post(
        reverse("job-application-list-create"),
        data={**valid_application_payload(), "owner": other_user.pk},
        format="json",
    )

    assert response.status_code == 201
    application = JobApplication.objects.get()
    assert application.owner == user
    assert application.title == "Backend Engineer"


@pytest.mark.django_db
def test_application_api_detail_hides_other_users_records(api_client) -> None:
    """Users should receive 404 for another user's application detail."""
    user = UserFactory()
    other_application = JobApplicationFactory(owner=UserFactory())
    api_client.force_authenticate(user=user)

    response = api_client.get(
        reverse("job-application-detail", kwargs={"pk": other_application.pk})
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_application_api_update_hides_other_users_records(api_client) -> None:
    """Users should not be able to update another user's application."""
    user = UserFactory()
    other_application = JobApplicationFactory(
        owner=UserFactory(),
        title="Original Role",
    )
    api_client.force_authenticate(user=user)

    response = api_client.patch(
        reverse("job-application-detail", kwargs={"pk": other_application.pk}),
        data={"title": "Changed Role"},
        format="json",
    )

    other_application.refresh_from_db()
    assert response.status_code == 404
    assert other_application.title == "Original Role"


@pytest.mark.django_db
def test_application_api_delete_hides_other_users_records(api_client) -> None:
    """Users should not be able to delete another user's application."""
    user = UserFactory()
    other_application = JobApplicationFactory(owner=UserFactory())
    api_client.force_authenticate(user=user)

    response = api_client.delete(
        reverse("job-application-detail", kwargs={"pk": other_application.pk})
    )

    assert response.status_code == 404
    assert JobApplication.objects.filter(pk=other_application.pk).exists()
