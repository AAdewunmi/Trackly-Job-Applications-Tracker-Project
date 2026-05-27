"""Smoke tests for dashboard routing."""

import pytest
from django.test import Client
from django.urls import reverse

from apps.roles.factories import AdminRoleFactory
from apps.users.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_root_renders_landing_page_for_anonymous_users(client: Client) -> None:
    """The root URL renders the public landing page."""
    response = client.get("/")

    assert response.status_code == 200
    assert b"Keep your job search organised." in response.content
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


def test_user_dashboard_requires_login(client: Client) -> None:
    """Anonymous users are redirected away from the dashboard."""
    response = client.get(reverse("dashboard:user"))

    assert response.status_code == 302
    assert response["Location"].startswith(f"{reverse('users:login')}?next=")


def test_user_dashboard_returns_success_for_authenticated_user(client: Client) -> None:
    """The user dashboard route is reachable for signed-in users."""
    user = UserFactory()
    client.force_login(user)

    response = client.get(reverse("dashboard:user"))

    assert response.status_code == 200
    assert b"Dashboard" in response.content


def test_admin_dashboard_requires_login(client: Client) -> None:
    """Anonymous users are redirected away from the admin dashboard."""
    response = client.get(reverse("dashboard:admin"))

    assert response.status_code == 302
    assert response["Location"].startswith(f"{reverse('users:login')}?next=")


def test_admin_dashboard_allows_staff_users(client: Client) -> None:
    """Staff users can view the admin dashboard."""
    user = UserFactory(is_staff=True)
    client.force_login(user)

    response = client.get(reverse("dashboard:admin"))

    assert response.status_code == 200
    assert b"Admin Dashboard" in response.content
    assert response.context["total_users"] == 1


def test_admin_dashboard_allows_active_admin_role(client: Client) -> None:
    """Users with the active Trackly admin role can view the admin dashboard."""
    role = AdminRoleFactory()
    user = UserFactory(roles=[role])
    client.force_login(user)

    response = client.get(reverse("dashboard:admin"))

    assert response.status_code == 200
    assert response.context["total_roles"] == 1


def test_admin_dashboard_denies_non_admin_users(client: Client) -> None:
    """Users without admin access receive a 403."""
    user = UserFactory()
    client.force_login(user)

    response = client.get(reverse("dashboard:admin"))

    assert response.status_code == 403
