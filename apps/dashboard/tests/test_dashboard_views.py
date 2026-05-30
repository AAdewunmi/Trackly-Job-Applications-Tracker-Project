"""Integration tests for Trackly dashboard access control."""

import pytest
from django.urls import reverse

from apps.roles.factories import AdminRoleFactory
from apps.users.factories import StaffUserFactory, UserFactory


@pytest.mark.django_db
def test_user_dashboard_requires_login(client) -> None:
    """Anonymous users should be redirected before viewing the dashboard."""
    response = client.get(reverse("dashboard:user"))

    assert response.status_code == 302
    assert reverse("users:login") in response.url


@pytest.mark.django_db
def test_user_dashboard_loads_for_authenticated_user(client) -> None:
    """Authenticated users should be able to load the dashboard."""
    user = UserFactory(email="dashboard@example.com")
    client.force_login(user)

    response = client.get(reverse("dashboard:user"))

    assert response.status_code == 200
    assert b"Your job search command centre" in response.content
    assert reverse("jobs:application_create").encode() in response.content
    assert reverse("jobs:application_list").encode() in response.content
    content = response.content.decode()
    assert content.index('id="pipeline"') < content.index('id="applications"')
    assert content.index('id="applications"') < content.index('id="metrics"')
    assert content.index('id="metrics"') < content.index('id="insights"')
    assert content.index('id="insights"') < content.index('id="empty-state"')
    assert content.index('id="empty-state"') < content.index('id="profile"')


@pytest.mark.django_db
def test_admin_dashboard_requires_login(client) -> None:
    """Anonymous visitors should be redirected before admin dashboard access."""
    response = client.get(reverse("dashboard:admin"))

    assert response.status_code == 302
    assert reverse("users:login") in response.url


@pytest.mark.django_db
def test_staff_user_can_access_admin_dashboard(client) -> None:
    """Django staff users should be allowed into the admin product surface."""
    user = StaffUserFactory(email="staff@example.com")
    client.force_login(user)

    response = client.get(reverse("dashboard:admin"))

    assert response.status_code == 200
    assert b"Trackly admin dashboard" in response.content
    assert reverse("dashboard:admin").encode() in response.content
    assert response.context["total_users"] == 1


@pytest.mark.django_db
def test_user_with_admin_role_can_access_admin_dashboard(client) -> None:
    """Users assigned the Trackly admin role should access the admin dashboard."""
    admin_role = AdminRoleFactory()
    user = UserFactory(email="role-admin@example.com")
    user.roles.add(admin_role)
    client.force_login(user)

    response = client.get(reverse("dashboard:admin"))

    assert response.status_code == 200
    assert b"Trackly admin dashboard" in response.content
    assert response.context["total_roles"] == 1


@pytest.mark.django_db
def test_non_admin_user_gets_forbidden_on_admin_dashboard(client) -> None:
    """Authenticated users without admin access should receive HTTP 403."""
    user = UserFactory(email="member@example.com")
    client.force_login(user)

    response = client.get(reverse("dashboard:admin"))

    assert response.status_code == 403
