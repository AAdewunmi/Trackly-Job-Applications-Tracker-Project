"""Smoke tests for dashboard routing."""

import pytest
from django.test import Client
from django.urls import reverse

from apps.users.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_root_renders_landing_page_for_anonymous_users(client: Client) -> None:
    """The root URL renders the public landing page."""
    response = client.get("/")

    assert response.status_code == 200
    assert b"Keep your job search organized." in response.content
    assert b"Create account" in response.content
    assert b"Sign in" in response.content


def test_root_renders_authenticated_actions(client: Client) -> None:
    """Authenticated users see dashboard and profile actions."""
    user = UserFactory()
    client.force_login(user)

    response = client.get("/")

    assert response.status_code == 200
    assert reverse("dashboard:user").encode() in response.content
    assert reverse("users:profile").encode() in response.content


def test_user_dashboard_returns_success(client: Client) -> None:
    """The user dashboard route is reachable."""
    response = client.get(reverse("dashboard:user"))

    assert response.status_code == 200
