"""Dashboard service layer for Trackly."""

from dataclasses import dataclass
from typing import Any

from apps.jobs.selectors import get_recent_applications_for_user
from apps.jobs.services import get_user_pipeline_metrics


@dataclass(frozen=True)
class DashboardContext:
    """Structured data needed to render the user dashboard."""

    metrics: dict[str, int]
    recent_applications: Any


def get_user_dashboard_context(user) -> DashboardContext:
    """Return user-scoped dashboard metrics and recent application activity."""
    return DashboardContext(
        metrics=get_user_pipeline_metrics(user),
        recent_applications=get_recent_applications_for_user(user, limit=5),
    )
