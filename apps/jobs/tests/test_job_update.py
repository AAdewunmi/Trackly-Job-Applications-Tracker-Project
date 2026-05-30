"""Integration tests for updating job applications."""

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.jobs.factories import JobApplicationFactory
from apps.jobs.models import JobApplication
from apps.users.factories import UserFactory


def valid_update_data(**overrides: object) -> dict[str, object]:
    """Return valid POST data for updating a job application."""
    data = {
        "title": "Updated Backend Engineer",
        "company": "Updated Ltd",
        "status": JobApplication.Status.INTERVIEWING,
        "job_link": "https://example.com/jobs/updated",
        "applied_date": timezone.localdate().isoformat(),
        "job_description": "Updated job description.",
        "notes": "Updated notes.",
    }
    data.update(overrides)
    return data


@pytest.mark.django_db
def test_application_update_page_renders_for_owner(client) -> None:
    """The owner should be able to open the edit form."""
    user = UserFactory()
    application = JobApplicationFactory(owner=user)
    client.force_login(user)

    response = client.get(
        reverse("jobs:application_update", kwargs={"pk": application.pk})
    )

    assert response.status_code == 200
    assert b"Edit job application" in response.content


@pytest.mark.django_db
def test_owner_can_update_application(client) -> None:
    """Posting valid update data should change the existing application."""
    user = UserFactory()
    application = JobApplicationFactory(owner=user)
    client.force_login(user)

    response = client.post(
        reverse("jobs:application_update", kwargs={"pk": application.pk}),
        data=valid_update_data(),
    )

    assert response.status_code == 302
    application.refresh_from_db()
    assert application.title == "Updated Backend Engineer"
    assert application.status == JobApplication.Status.INTERVIEWING


@pytest.mark.django_db
def test_invalid_update_does_not_change_application(client) -> None:
    """Invalid updates should re-render the form and preserve stored data."""
    user = UserFactory()
    application = JobApplicationFactory(
        owner=user,
        title="Original Title",
        status=JobApplication.Status.SAVED,
    )
    client.force_login(user)

    response = client.post(
        reverse("jobs:application_update", kwargs={"pk": application.pk}),
        data=valid_update_data(status="invalid-status"),
    )

    assert response.status_code == 200
    application.refresh_from_db()
    assert application.title == "Original Title"
    assert application.status == JobApplication.Status.SAVED
