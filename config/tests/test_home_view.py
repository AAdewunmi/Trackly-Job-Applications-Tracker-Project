"""Tests for the public Trackly landing page."""

import pytest
from apps.users.factories import UserFactory
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_root_renders_landing_page_for_anonymous_users(client) -> None:
    """The root URL renders the public landing page."""
    response = client.get("/")

    assert response.status_code == 200
    assert b"Keep your job search organised." in response.content
    assert b"Create account" in response.content
    assert b"Sign in" in response.content
    assert b"img/user-dashboard-preview.png" in response.content


def test_root_renders_authenticated_actions(client) -> None:
    """Authenticated users see dashboard and profile actions."""
    user = UserFactory()
    client.force_login(user)

    response = client.get("/")

    assert response.status_code == 200
    assert reverse("dashboard:user").encode() in response.content
    assert reverse("jobs:application_list").encode() in response.content
    assert reverse("users:profile").encode() in response.content
