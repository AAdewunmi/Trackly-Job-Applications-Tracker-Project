"""View tests for Trackly job application workflows."""

import pytest
from django.urls import reverse

from apps.jobs.models import JobApplication
from apps.users.factories import UserFactory


@pytest.mark.django_db
def test_application_detail_requires_login(client) -> None:
    """Anonymous users should be redirected before viewing applications."""
    owner = UserFactory()
    application = JobApplication.objects.create(
        owner=owner,
        title="Product Analyst",
        company="Example Co",
    )

    response = client.get(application.get_absolute_url())

    assert response.status_code == 302
    assert reverse("users:login") in response.url


@pytest.mark.django_db
def test_application_detail_loads_for_owner(client) -> None:
    """Application owners should be able to view their detail page."""
    owner = UserFactory()
    application = JobApplication.objects.create(
        owner=owner,
        title="Product Analyst",
        company="Example Co",
    )
    client.force_login(owner)

    response = client.get(application.get_absolute_url())

    assert response.status_code == 200
    assert response.context["application"] == application
    assert b"Product Analyst" in response.content


@pytest.mark.django_db
def test_application_detail_hides_other_users_applications(client) -> None:
    """Users should not be able to view applications they do not own."""
    owner = UserFactory(email="owner@example.com")
    other_user = UserFactory(email="other@example.com")
    application = JobApplication.objects.create(
        owner=owner,
        title="Product Analyst",
        company="Example Co",
    )
    client.force_login(other_user)

    response = client.get(application.get_absolute_url())

    assert response.status_code == 404
