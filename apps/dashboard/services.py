"""Dashboard service layer for Trackly."""

from dataclasses import dataclass
from typing import Any

from apps.jobs.models import JobApplication
from apps.jobs.selectors import (
    get_recent_applications_for_user,
    get_recent_applications_for_user_by_status,
)
from apps.jobs.services import get_user_pipeline_metrics


@dataclass(frozen=True)
class DashboardContext:
    """Structured data needed to render the user dashboard."""

    metrics: dict[str, int]
    recent_applications: Any
    saved_applications: Any
    applied_applications: Any
    interviewing_applications: Any


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
    )
