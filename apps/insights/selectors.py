"""
Read-side selectors for Trackly insights.

Selectors centralise query behaviour so templates, services, and tests do not
duplicate ownership filtering rules.
"""

from dataclasses import dataclass

from django.contrib.auth.models import AnonymousUser
from django.db.models import Avg, Count, Max, QuerySet

from apps.insights.models import JobInsight, TargetRoleProfile
from apps.jobs.models import JobApplication

INSIGHT_SORT_OPTIONS = {
    "recent": "-created_at",
    "score_desc": "-similarity_score",
    "score_asc": "similarity_score",
    "role": "job_application__title",
    "target_profile": "target_profile__title",
}


@dataclass(frozen=True)
class InsightScoreBucket:
    """Chart-ready count for one TF-IDF score range."""

    label: str
    count: int
    percentage: int


@dataclass(frozen=True)
class TargetProfileMatchSummary:
    """Chart-ready match summary for one target role profile."""

    title: str
    insight_count: int
    average_score: float
    best_score: float
    percentage: int


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


def get_filtered_insights_for_user(
    user,
    *,
    target_profile_id: str = "",
    score_label: str = "",
    sort: str = "recent",
) -> QuerySet[JobInsight]:
    """Return user-owned insights filtered and ordered for the insights page."""
    insights = get_insights_for_user(user)

    if target_profile_id:
        insights = insights.filter(target_profile_id=target_profile_id)

    if score_label:
        insights = insights.filter(score_label=score_label)

    order_by = INSIGHT_SORT_OPTIONS.get(sort, INSIGHT_SORT_OPTIONS["recent"])
    return insights.order_by(order_by, "-created_at")


def get_score_labels_for_user(user) -> list[str]:
    """Return distinct score labels available in a user's stored insights."""
    if not _is_authenticated_user(user):
        return []

    return list(
        get_insights_for_user(user)
        .order_by("score_label")
        .values_list("score_label", flat=True)
        .distinct()
    )


def get_recent_insights_for_user(user, limit: int = 10) -> list[JobInsight]:
    """Return a bounded list of recent insights owned by a user."""
    return list(get_insights_for_user(user)[:limit])


def _percentage(part: int | float, total: int | float) -> int:
    """Return a whole-number percentage while avoiding division by zero."""
    if total == 0:
        return 0

    return round((part / total) * 100)


def get_insight_score_histogram_for_user(user) -> list[InsightScoreBucket]:
    """Return user-owned insight score distribution buckets."""
    buckets = [
        ("Low match", 0.0, 0.25),
        ("Partial match", 0.25, 0.5),
        ("Strong match", 0.5, 0.75),
        ("Excellent match", 0.75, 1.01),
    ]
    insights = get_insights_for_user(user)
    total_insights = insights.count()
    score_counts = [
        insights.filter(
            similarity_score__gte=lower_bound,
            similarity_score__lt=upper_bound,
        ).count()
        for _, lower_bound, upper_bound in buckets
    ]

    return [
        InsightScoreBucket(
            label=label,
            count=count,
            percentage=_percentage(count, total_insights),
        )
        for count, (label, _, _) in zip(score_counts, buckets, strict=True)
    ]


def get_target_profile_match_summaries_for_user(
    user,
) -> list[TargetProfileMatchSummary]:
    """Return average and best insight scores grouped by target profile."""
    rows = (
        get_insights_for_user(user)
        .values("target_profile__title")
        .annotate(
            insight_count=Count("id"),
            average_score=Avg("similarity_score"),
            best_score=Max("similarity_score"),
        )
        .order_by("-average_score", "target_profile__title")
    )

    return [
        TargetProfileMatchSummary(
            title=row["target_profile__title"],
            insight_count=row["insight_count"],
            average_score=round(row["average_score"] or 0, 2),
            best_score=round(row["best_score"] or 0, 2),
            percentage=_percentage(row["average_score"] or 0, 1),
        )
        for row in rows
    ]
