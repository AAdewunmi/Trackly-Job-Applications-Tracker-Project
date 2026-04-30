"""Smoke tests for dashboard routing."""

from django.test import Client
from django.urls import reverse


def test_root_redirects_to_user_dashboard(client: Client) -> None:
    """The root URL redirects to the user dashboard route."""
    response = client.get("/")

    assert response.status_code == 302
    assert response["Location"] == reverse("dashboard:user")


def test_user_dashboard_returns_success(client: Client) -> None:
    """The user dashboard route is reachable."""
    response = client.get(reverse("dashboard:user"))

    assert response.status_code == 200
