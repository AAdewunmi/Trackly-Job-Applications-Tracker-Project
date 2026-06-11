"""Tests for user dashboard metrics and rendering."""

import pytest
from django.urls import reverse

from apps.dashboard.services import (
    get_admin_application_table_page,
    get_admin_dashboard_context,
    get_user_dashboard_context,
)
from apps.insights.factories import JobInsightFactory, TargetRoleProfileFactory
from apps.jobs.factories import ApplicationNoteFactory, JobApplicationFactory
from apps.jobs.models import JobApplication
from apps.roles.factories import AdminRoleFactory
from apps.users.factories import UserFactory


@pytest.mark.django_db
def test_dashboard_context_returns_empty_metrics_for_new_user() -> None:
    """A new user should receive zeroed dashboard metrics."""
    user = UserFactory()

    context = get_user_dashboard_context(user)

    assert context.metrics == {
        "total_applications": 0,
        "active_applications": 0,
        "saved_jobs": 0,
        "follow_ups": 0,
        "interviews": 0,
        "offers": 0,
        "rejections": 0,
        "notes": 0,
    }


@pytest.mark.django_db
def test_dashboard_context_counts_only_current_user_data() -> None:
    """Dashboard metrics should not include another user's records."""
    user = UserFactory()
    other_user = UserFactory()
    applied_application = JobApplicationFactory(
        owner=user,
        status=JobApplication.Status.APPLIED,
    )
    JobApplicationFactory(
        owner=user,
        status=JobApplication.Status.INTERVIEWING,
    )
    JobApplicationFactory(
        owner=user,
        status=JobApplication.Status.OFFER,
    )
    JobApplicationFactory(
        owner=other_user,
        status=JobApplication.Status.REJECTED,
    )
    ApplicationNoteFactory(application=applied_application)
    ApplicationNoteFactory(application=applied_application)

    context = get_user_dashboard_context(user)

    assert context.metrics["total_applications"] == 3
    assert context.metrics["active_applications"] == 2
    assert context.metrics["saved_jobs"] == 0
    assert context.metrics["follow_ups"] == 0
    assert context.metrics["interviews"] == 1
    assert context.metrics["offers"] == 1
    assert context.metrics["rejections"] == 0
    assert context.metrics["notes"] == 2
    assert list(context.recent_insights) == []
    assert list(context.target_profiles) == []


@pytest.mark.django_db
def test_admin_dashboard_context_returns_platform_metrics() -> None:
    """Admin metrics should summarize records across the platform."""
    AdminRoleFactory()
    user = UserFactory()
    saved_application = JobApplicationFactory(
        owner=user,
        status=JobApplication.Status.SAVED,
    )
    JobApplicationFactory(
        owner=user,
        status=JobApplication.Status.INTERVIEWING,
    )
    ApplicationNoteFactory(application=saved_application)
    TargetRoleProfileFactory(owner=user, is_active=True)
    TargetRoleProfileFactory(owner=user, is_active=False)
    JobInsightFactory(job_application=saved_application)

    context = get_admin_dashboard_context()

    assert context.total_users == 1
    assert context.total_roles == 1
    assert context.total_applications == 2
    assert context.total_notes == 1
    assert context.total_target_profiles == 3
    assert context.active_target_profiles == 2
    assert context.total_generated_insights == 1
    assert {
        status_count.status: status_count.count
        for status_count in context.application_status_counts
    } == {
        JobApplication.Status.SAVED: 1,
        JobApplication.Status.APPLIED: 0,
        JobApplication.Status.SCREENING: 0,
        JobApplication.Status.INTERVIEWING: 1,
        JobApplication.Status.OFFER: 0,
        JobApplication.Status.REJECTED: 0,
        JobApplication.Status.WITHDRAWN: 0,
    }
    assert {
        status_count.status: status_count.percentage
        for status_count in context.application_status_counts
    }[JobApplication.Status.SAVED] == 50
    assert context.application_page.paginator.count == 2


@pytest.mark.django_db
def test_admin_application_table_page_filters_search_status_and_sort() -> None:
    """Admin application table data should support dashboard controls."""
    user = UserFactory(email="owner@example.com")
    saved_application = JobApplicationFactory(
        owner=user,
        title="Backend Engineer",
        company="Acme",
        status=JobApplication.Status.SAVED,
    )
    JobApplicationFactory(
        title="Product Designer",
        company="Beta",
        status=JobApplication.Status.INTERVIEWING,
    )

    page = get_admin_application_table_page(
        search="backend",
        status=JobApplication.Status.SAVED,
        sort="company",
    )

    assert page.paginator.count == 1
    assert list(page.object_list) == [saved_application]


@pytest.mark.django_db
def test_user_dashboard_requires_authentication(client) -> None:
    """Anonymous users should be redirected from the dashboard."""
    response = client.get(reverse("dashboard:user"))

    assert response.status_code == 302


@pytest.mark.django_db
def test_user_dashboard_renders_actionable_empty_state(client) -> None:
    """New users should see a clear first-application action."""
    user = UserFactory()
    client.force_login(user)

    response = client.get(reverse("dashboard:user"))

    assert response.status_code == 200
    assert b"Add your first role" in response.content
    assert b"View applications" in response.content
    assert b"Add application" in response.content


@pytest.mark.django_db
def test_user_dashboard_renders_metrics(client) -> None:
    """The dashboard should render metrics generated by the service layer."""
    user = UserFactory()
    JobApplicationFactory(owner=user, status=JobApplication.Status.SAVED)
    JobApplicationFactory(owner=user, status=JobApplication.Status.APPLIED)
    JobApplicationFactory(owner=user, status=JobApplication.Status.SCREENING)
    JobApplicationFactory(owner=user, status=JobApplication.Status.INTERVIEWING)
    JobApplicationFactory(owner=user, status=JobApplication.Status.REJECTED)
    client.force_login(user)

    response = client.get(reverse("dashboard:user"))

    assert response.status_code == 200
    assert response.context["metrics"]["total_applications"] == 5
    assert response.context["metrics"]["active_applications"] == 3
    assert response.context["metrics"]["saved_jobs"] == 1
    assert response.context["metrics"]["follow_ups"] == 1
    assert response.context["metrics"]["interviews"] == 1
    assert response.context["metrics"]["rejections"] == 1
    assert b"Saved jobs" in response.content
    assert b"Follow-ups" in response.content
    assert b"Interviews" in response.content
    assert b"Total Applications" in response.content
    assert b"Active Applications" in response.content
    assert b"Offers" in response.content
    assert b"Rejections" in response.content
    assert b"Notes" in response.content


@pytest.mark.django_db
def test_user_dashboard_renders_status_grouped_pipeline_cards(client) -> None:
    """The dashboard should render user-owned cards in pipeline columns."""
    user = UserFactory()
    saved_application = JobApplicationFactory(
        owner=user,
        title="Saved Platform Engineer",
        status=JobApplication.Status.SAVED,
    )
    applied_application = JobApplicationFactory(
        owner=user,
        title="Applied Platform Engineer",
        status=JobApplication.Status.APPLIED,
    )
    interview_application = JobApplicationFactory(
        owner=user,
        title="Interview Platform Engineer",
        status=JobApplication.Status.INTERVIEWING,
    )
    client.force_login(user)

    response = client.get(reverse("dashboard:user"))

    assert response.status_code == 200
    assert list(response.context["saved_applications"]) == [saved_application]
    assert list(response.context["applied_applications"]) == [applied_application]
    assert list(response.context["interviewing_applications"]) == [
        interview_application
    ]
    assert saved_application.title.encode() in response.content
    assert applied_application.title.encode() in response.content
    assert interview_application.title.encode() in response.content


@pytest.mark.django_db
def test_user_dashboard_renders_live_insights_summary(client) -> None:
    """The dashboard insight card should reflect available backend functionality."""
    user = UserFactory()
    profile = TargetRoleProfileFactory(owner=user, title="Backend Target")
    insight = JobInsightFactory(
        job_application__owner=user,
        job_application__title="Django API Engineer",
        target_profile=profile,
        score_label="Strong match",
    )
    JobInsightFactory()
    client.force_login(user)

    response = client.get(reverse("dashboard:user"))

    assert response.status_code == 200
    assert list(response.context["target_profiles"]) == [profile]
    assert list(response.context["recent_insights"]) == [insight]
    assert b"Generate explainable job-fit insights" in response.content
    assert b"Live" in response.content
    assert b"Strong match" in response.content
    assert b"Django API Engineer" in response.content
    assert reverse("insights:insight-list").encode() in response.content
    assert reverse("insights:target-profile-create").encode() in response.content
