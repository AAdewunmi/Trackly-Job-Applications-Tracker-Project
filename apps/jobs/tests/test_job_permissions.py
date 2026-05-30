"""Permission tests for user-owned job application routes."""

import pytest
from django.urls import reverse

from apps.jobs.factories import JobApplicationFactory
from apps.users.factories import UserFactory


@pytest.mark.django_db
def test_owner_can_view_application_detail(client) -> None:
    """The owner should be able to view their application detail page."""
    user = UserFactory()
    application = JobApplicationFactory(owner=user)
    client.force_login(user)

    response = client.get(
        reverse("jobs:application_detail", kwargs={"pk": application.pk})
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_user_cannot_view_another_users_application_detail(client) -> None:
    """A different user should receive a 404 for another user's record."""
    user = UserFactory()
    other_user = UserFactory()
    application = JobApplicationFactory(owner=other_user)
    client.force_login(user)

    response = client.get(
        reverse("jobs:application_detail", kwargs={"pk": application.pk})
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_user_cannot_open_edit_page_for_another_users_application(client) -> None:
    """The update page should be scoped by the current owner."""
    user = UserFactory()
    other_user = UserFactory()
    application = JobApplicationFactory(owner=other_user)
    client.force_login(user)

    response = client.get(
        reverse("jobs:application_update", kwargs={"pk": application.pk})
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_user_cannot_open_delete_page_for_another_users_application(client) -> None:
    """The delete page should be scoped by the current owner."""
    user = UserFactory()
    other_user = UserFactory()
    application = JobApplicationFactory(owner=other_user)
    client.force_login(user)

    response = client.get(
        reverse("jobs:application_delete", kwargs={"pk": application.pk})
    )

    assert response.status_code == 404
