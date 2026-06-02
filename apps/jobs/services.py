"""Business services for job application metrics and workflow reporting."""

from django.db.models import Count

from apps.jobs.models import JobApplication
from apps.jobs.selectors import application_queryset_for_user, get_note_count_for_user

ACTIVE_STATUSES = (
    JobApplication.Status.APPLIED,
    JobApplication.Status.SCREENING,
    JobApplication.Status.INTERVIEWING,
)


def get_application_status_counts(user) -> dict[str, int]:
    """Return user-scoped application counts grouped by workflow status."""
    counts = {status: 0 for status in JobApplication.Status.values}
    rows = (
        application_queryset_for_user(user).values("status").annotate(count=Count("id"))
    )

    for row in rows:
        counts[row["status"]] = row["count"]

    return counts


def get_user_pipeline_metrics(user) -> dict[str, int]:
    """Return dashboard-ready job search metrics for one user."""
    status_counts = get_application_status_counts(user)
    total_applications = sum(status_counts.values())
    active_applications = sum(status_counts[status] for status in ACTIVE_STATUSES)

    return {
        "total_applications": total_applications,
        "active_applications": active_applications,
        "saved_jobs": status_counts[JobApplication.Status.SAVED],
        "follow_ups": status_counts[JobApplication.Status.SCREENING],
        "interviews": status_counts[JobApplication.Status.INTERVIEWING],
        "offers": status_counts[JobApplication.Status.OFFER],
        "rejections": status_counts[JobApplication.Status.REJECTED],
        "notes": get_note_count_for_user(user),
    }
