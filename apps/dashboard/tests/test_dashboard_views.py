"""Integration tests for Trackly dashboard access control."""

import pytest
from django.urls import reverse

from apps.insights.factories import JobInsightFactory, TargetRoleProfileFactory
from apps.jobs.factories import ApplicationNoteFactory, JobApplicationFactory
from apps.jobs.models import JobApplication
from apps.roles.factories import AdminRoleFactory
from apps.users.factories import StaffUserFactory, UserFactory


@pytest.mark.django_db
def test_user_dashboard_requires_login(client) -> None:
    """Anonymous users should be redirected before viewing the dashboard."""
    response = client.get(reverse("dashboard:user"))

    assert response.status_code == 302
    assert reverse("users:login") in response.url


@pytest.mark.django_db
def test_user_dashboard_preview_route_does_not_exist(client) -> None:
    """The temporary unauthenticated dashboard preview route should stay removed."""
    response = client.get("/dashboard/preview/")

    assert response.status_code == 404


@pytest.mark.django_db
def test_user_dashboard_loads_for_authenticated_user(client) -> None:
    """Authenticated users should be able to load the dashboard."""
    user = UserFactory(email="dashboard@example.com")
    application = JobApplicationFactory(
        owner=user,
        status=JobApplication.Status.INTERVIEWING,
    )
    ApplicationNoteFactory(application=application)
    client.force_login(user)

    response = client.get(reverse("dashboard:user"))

    assert response.status_code == 200
    assert response.context["metrics"]["total_applications"] == 1
    assert response.context["metrics"]["interviews"] == 1
    assert response.context["metrics"]["notes"] == 1
    assert list(response.context["recent_applications"]) == [application]
    assert b"Your job search command centre" in response.content
    assert reverse("jobs:application_create").encode() in response.content
    assert reverse("jobs:application_list").encode() in response.content
    content = response.content.decode()
    assert content.index('id="pipeline"') < content.index('id="applications"')
    assert content.index('id="applications"') < content.index('id="metrics"')
    assert content.index('id="metrics"') < content.index('id="insights"')
    assert content.index('id="insights"') < content.index('id="profile"')


@pytest.mark.django_db
def test_staff_user_cannot_access_user_dashboard(client) -> None:
    """Django staff users should be kept out of end-user dashboard flows."""
    user = StaffUserFactory(email="staff-dashboard@example.com")
    client.force_login(user)

    response = client.get(reverse("dashboard:user"))

    assert response.status_code == 403


@pytest.mark.django_db
def test_user_with_admin_role_cannot_access_user_dashboard(client) -> None:
    """Trackly admin-role users should be kept out of end-user dashboard flows."""
    admin_role = AdminRoleFactory()
    user = UserFactory(email="role-admin-dashboard@example.com")
    user.roles.add(admin_role)
    client.force_login(user)

    response = client.get(reverse("dashboard:user"))

    assert response.status_code == 403


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
    application = JobApplicationFactory(
        owner=user,
        status=JobApplication.Status.APPLIED,
    )
    ApplicationNoteFactory(application=application)
    TargetRoleProfileFactory(owner=user)
    JobInsightFactory(job_application=application)
    client.force_login(user)

    response = client.get(reverse("dashboard:admin"))

    assert response.status_code == 200
    assert b"Trackly admin dashboard" in response.content
    assert reverse("dashboard:admin").encode() in response.content
    assert f'href="{reverse("dashboard:user")}"'.encode() not in response.content
    assert f'href="{reverse("jobs:application_list")}"'.encode() not in response.content
    assert response.context["total_users"] == 1
    assert response.context["admin_context"].total_applications == 1
    assert response.context["admin_context"].total_notes == 1
    assert response.context["admin_context"].total_target_profiles == 2
    assert response.context["admin_context"].total_generated_insights == 1
    assert response.context["admin_context"].application_page.paginator.count == 1
    assert b"Applications by status" in response.content
    assert b"Generated insights" in response.content
    assert b"Control centre" in response.content
    assert b"Title, company, or owner" in response.content
    assert b"Applied" in response.content


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
