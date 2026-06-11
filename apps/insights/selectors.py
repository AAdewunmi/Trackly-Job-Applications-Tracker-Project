"""
Read-side selectors for Trackly insights.

Selectors centralise query behaviour so templates, services, and tests do not
duplicate ownership filtering rules.
"""

from django.contrib.auth.models import AnonymousUser
from django.db.models import QuerySet

from apps.insights.models import JobInsight, TargetRoleProfile
from apps.jobs.models import JobApplication


def _is_authenticated_user(user) -> bool:
    """Return whether a user can be used for ownership-scoped queries."""
    return not (
        isinstance(user, AnonymousUser)
        or not user.is_authenticated
        or not getattr(user, "pk", None)
    )


def get_target_profiles_for_user(user) -> QuerySet[TargetRoleProfile]:
    """Return active and inactive target profiles owned by a user."""
    if not _is_authenticated_user(user):
        return TargetRoleProfile.objects.none()

    return TargetRoleProfile.objects.filter(owner=user).order_by(
        "-is_active",
        "title",
    )


def get_active_target_profiles_for_user(user) -> QuerySet[TargetRoleProfile]:
    """Return active target profiles owned by a user."""
    if not _is_authenticated_user(user):
        return TargetRoleProfile.objects.none()

    return TargetRoleProfile.objects.filter(owner=user, is_active=True).order_by(
        "title"
    )


def get_latest_insight_for_application(
    application: JobApplication,
) -> JobInsight | None:
    """Return the latest stored insight for an application."""
    return application.insights.select_related("target_profile").first()


def get_insights_for_user(user) -> QuerySet[JobInsight]:
    """Return stored insights connected to applications owned by a user."""
    if not _is_authenticated_user(user):
        return JobInsight.objects.none()

    return (
        JobInsight.objects.select_related("job_application", "target_profile")
        .filter(job_application__owner=user)
        .order_by("-created_at")
    )


def get_recent_insights_for_user(user, limit: int = 10) -> list[JobInsight]:
    """Return a bounded list of recent insights owned by a user."""
    return list(get_insights_for_user(user)[:limit])
