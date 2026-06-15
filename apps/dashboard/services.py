"""Dashboard service layer for Trackly."""

from dataclasses import dataclass
from typing import Any

from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Count, Q

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
from apps.jobs.services import get_application_status_counts, get_user_pipeline_metrics
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
    status_chart: list["ChartMetric"]
    funnel_chart: list["ChartMetric"]


@dataclass(frozen=True)
class ApplicationStatusCount:
    """Application count for one workflow status."""

    status: str
    label: str
    count: int
    percentage: int


@dataclass(frozen=True)
class ChartMetric:
    """Chart-ready metric with a label, count, and display percentage."""

    label: str
    count: int
    percentage: int


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
    application_page: Any
    application_search: str
    application_status: str
    application_sort: str
    platform_activity_counts: list[ChartMetric]


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
        status_chart=get_user_application_status_chart(user),
        funnel_chart=get_user_job_search_funnel(user),
    )


def _percentage(part: int, total: int) -> int:
    """Return a whole-number percentage while avoiding division by zero."""
    if total == 0:
        return 0

    return round((part / total) * 100)


def _relative_chart_metrics(metrics: list[tuple[str, int]]) -> list[ChartMetric]:
    """Return chart metrics scaled against the largest current value."""
    max_count = max((count for _, count in metrics), default=0)

    return [
        ChartMetric(
            label=label,
            count=count,
            percentage=_percentage(count, max_count),
        )
        for label, count in metrics
    ]


def get_user_application_status_chart(user) -> list[ChartMetric]:
    """Return user application status distribution for dashboard charts."""
    status_counts = get_application_status_counts(user)
    total_applications = sum(status_counts.values())

    return [
        ChartMetric(
            label=label,
            count=status_counts[status],
            percentage=_percentage(status_counts[status], total_applications),
        )
        for status, label in JobApplication.Status.choices
    ]


def get_user_job_search_funnel(user) -> list[ChartMetric]:
    """Return current user pipeline stages as a funnel-shaped chart."""
    status_counts = get_application_status_counts(user)

    return _relative_chart_metrics(
        [
            ("Saved", status_counts[JobApplication.Status.SAVED]),
            ("Applied", status_counts[JobApplication.Status.APPLIED]),
            ("Screening", status_counts[JobApplication.Status.SCREENING]),
            ("Interviewing", status_counts[JobApplication.Status.INTERVIEWING]),
            ("Offer", status_counts[JobApplication.Status.OFFER]),
        ]
    )


def get_admin_platform_activity_counts() -> list[ChartMetric]:
    """Return platform activity totals scaled for an admin overview chart."""
    user_model = get_user_model()

    return _relative_chart_metrics(
        [
            ("Users", user_model.objects.count()),
            ("Applications", JobApplication.objects.count()),
            ("Notes", ApplicationNote.objects.count()),
            ("Target profiles", TargetRoleProfile.objects.count()),
            ("Insights", JobInsight.objects.count()),
        ]
    )


def get_application_status_counts_for_admin(
    total_applications: int | None = None,
) -> list[ApplicationStatusCount]:
    """Return platform-wide application counts grouped by workflow status."""
    rows = JobApplication.objects.values("status").annotate(count=Count("id"))
    counts_by_status = {row["status"]: row["count"] for row in rows}
    application_total = (
        total_applications
        if total_applications is not None
        else sum(counts_by_status.values())
    )

    return [
        ApplicationStatusCount(
            status=status,
            label=label,
            count=counts_by_status.get(status, 0),
            percentage=_percentage(counts_by_status.get(status, 0), application_total),
        )
        for status, label in JobApplication.Status.choices
    ]


def get_admin_application_table_page(
    *,
    search: str = "",
    status: str = "",
    sort: str = "-updated_at",
    page_number: int | str = 1,
    per_page: int = 5,
) -> Any:
    """Return a filtered, sorted, paginated page of platform applications."""
    allowed_sorts = {
        "-updated_at",
        "updated_at",
        "company",
        "status",
        "owner__email",
    }
    ordering = sort if sort in allowed_sorts else "-updated_at"
    applications = (
        JobApplication.objects.select_related("owner")
        .annotate(
            note_count=Count("application_notes", distinct=True),
            insight_count=Count("insights", distinct=True),
        )
        .order_by(ordering, "-id")
    )

    if search:
        applications = applications.filter(
            Q(title__icontains=search)
            | Q(company__icontains=search)
            | Q(owner__email__icontains=search)
        )

    if status in JobApplication.Status.values:
        applications = applications.filter(status=status)

    return Paginator(applications, per_page).get_page(page_number)


def get_admin_dashboard_context(
    *,
    application_search: str = "",
    application_status: str = "",
    application_sort: str = "-updated_at",
    application_page: int | str = 1,
) -> AdminDashboardContext:
    """Return platform-wide metrics for the protected admin dashboard."""
    user_model = get_user_model()
    total_applications = JobApplication.objects.count()

    return AdminDashboardContext(
        total_users=user_model.objects.count(),
        total_roles=Role.objects.count(),
        total_applications=total_applications,
        total_notes=ApplicationNote.objects.count(),
        total_target_profiles=TargetRoleProfile.objects.count(),
        active_target_profiles=TargetRoleProfile.objects.filter(is_active=True).count(),
        total_generated_insights=JobInsight.objects.count(),
        application_status_counts=get_application_status_counts_for_admin(
            total_applications=total_applications,
        ),
        application_page=get_admin_application_table_page(
            search=application_search,
            status=application_status,
            sort=application_sort,
            page_number=application_page,
        ),
        application_search=application_search,
        application_status=application_status,
        application_sort=application_sort,
        platform_activity_counts=get_admin_platform_activity_counts(),
    )
