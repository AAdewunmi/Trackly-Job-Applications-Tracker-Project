"""Service-layer helpers for Trackly job application metrics."""

from django.db.models import Count

from apps.jobs.models import JobApplication
from apps.jobs.selectors import (
    application_queryset_for_user,
    get_note_count_for_user,
)


def get_application_status_counts(user) -> dict[str, int]:
    """Return user-scoped application counts for every workflow status."""
    counts = {status: 0 for status in JobApplication.Status.values}
    status_rows = (
        application_queryset_for_user(user).values("status").annotate(count=Count("id"))
    )

    for row in status_rows:
        counts[row["status"]] = row["count"]

    return counts


def get_user_pipeline_metrics(user) -> dict[str, int]:
    """Return user-scoped dashboard metrics for the application pipeline."""
    status_counts = get_application_status_counts(user)
    active_statuses = (
        JobApplication.Status.APPLIED,
        JobApplication.Status.SCREENING,
        JobApplication.Status.INTERVIEWING,
    )

    return {
        "total_applications": sum(status_counts.values()),
        "active_applications": sum(status_counts[status] for status in active_statuses),
        "interviews": status_counts[JobApplication.Status.INTERVIEWING],
        "offers": status_counts[JobApplication.Status.OFFER],
        "rejections": status_counts[JobApplication.Status.REJECTED],
        "notes": get_note_count_for_user(user),
    }
