"""Integration tests for deleting job applications."""

import pytest
from django.urls import reverse

from apps.jobs.factories import JobApplicationFactory
from apps.jobs.models import JobApplication
from apps.users.factories import UserFactory


@pytest.mark.django_db
def test_application_delete_confirmation_renders_for_owner(client) -> None:
    """The owner should be able to open the delete confirmation page."""
    user = UserFactory()
    application = JobApplicationFactory(owner=user)
    client.force_login(user)

    response = client.get(
        reverse("jobs:application_delete", kwargs={"pk": application.pk})
    )

    assert response.status_code == 200
    assert b"Delete application" in response.content


@pytest.mark.django_db
def test_owner_can_delete_application(client) -> None:
    """Posting to the delete route should remove the owner's application."""
    user = UserFactory()
    application = JobApplicationFactory(owner=user)
    client.force_login(user)

    response = client.post(
        reverse("jobs:application_delete", kwargs={"pk": application.pk})
    )

    assert response.status_code == 302
    assert JobApplication.objects.filter(pk=application.pk).exists() is False


@pytest.mark.django_db
def test_delete_does_not_remove_other_users_application(client) -> None:
    """A user should not be able to delete another user's application."""
    user = UserFactory()
    other_user = UserFactory()
    application = JobApplicationFactory(owner=other_user)
    client.force_login(user)

    response = client.post(
        reverse("jobs:application_delete", kwargs={"pk": application.pk})
    )

    assert response.status_code == 404
    assert JobApplication.objects.filter(pk=application.pk).exists() is True
