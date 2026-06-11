"""Dashboard service layer for Trackly."""

from dataclasses import dataclass
from typing import Any

from django.contrib.auth import get_user_model
from django.db.models import Count

from apps.insights.models import JobInsight, TargetRoleProfile
from apps.insights.selectors import (
    get_recent_insights_for_user,
    get_target_profiles_for_user,
)
from apps.jobs.models import ApplicationNote, JobApplication
from apps.jobs.selectors import (
    get_recent_applications_for_user,
    get_recent_applications_for_user_by_status,
)
from apps.jobs.services import get_user_pipeline_metrics
from apps.roles.models import Role


@dataclass(frozen=True)
class DashboardContext:
    """Structured data needed to render the user dashboard."""

    metrics: dict[str, int]
    recent_applications: Any
    saved_applications: Any
    applied_applications: Any
    interviewing_applications: Any
    recent_insights: Any
    target_profiles: Any


@dataclass(frozen=True)
class ApplicationStatusCount:
    """Application count for one workflow status."""

    status: str
    label: str
    count: int


@dataclass(frozen=True)
class AdminDashboardContext:
    """Structured data needed to render platform-wide admin metrics."""

    total_users: int
    total_roles: int
    total_applications: int
    total_notes: int
    total_target_profiles: int
    active_target_profiles: int
    total_generated_insights: int
    application_status_counts: list[ApplicationStatusCount]


def get_user_dashboard_context(user) -> DashboardContext:
    """Return user-scoped dashboard metrics and recent application activity."""
    return DashboardContext(
        metrics=get_user_pipeline_metrics(user),
        recent_applications=get_recent_applications_for_user(user, limit=5),
        saved_applications=get_recent_applications_for_user_by_status(
            user,
            JobApplication.Status.SAVED,
            limit=5,
        ),
        applied_applications=get_recent_applications_for_user_by_status(
            user,
            JobApplication.Status.APPLIED,
            limit=5,
        ),
        interviewing_applications=get_recent_applications_for_user_by_status(
            user,
            JobApplication.Status.INTERVIEWING,
            limit=5,
        ),
        recent_insights=get_recent_insights_for_user(user, limit=3),
        target_profiles=get_target_profiles_for_user(user),
    )


def get_application_status_counts_for_admin() -> list[ApplicationStatusCount]:
    """Return platform-wide application counts grouped by workflow status."""
    rows = JobApplication.objects.values("status").annotate(count=Count("id"))
    counts_by_status = {row["status"]: row["count"] for row in rows}

    return [
        ApplicationStatusCount(
            status=status,
            label=label,
            count=counts_by_status.get(status, 0),
        )
        for status, label in JobApplication.Status.choices
    ]


def get_admin_dashboard_context() -> AdminDashboardContext:
    """Return platform-wide metrics for the protected admin dashboard."""
    user_model = get_user_model()

    return AdminDashboardContext(
        total_users=user_model.objects.count(),
        total_roles=Role.objects.count(),
        total_applications=JobApplication.objects.count(),
        total_notes=ApplicationNote.objects.count(),
        total_target_profiles=TargetRoleProfile.objects.count(),
        active_target_profiles=TargetRoleProfile.objects.filter(is_active=True).count(),
        total_generated_insights=JobInsight.objects.count(),
        application_status_counts=get_application_status_counts_for_admin(),
    )
