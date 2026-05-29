"""Read-only query helpers for Trackly job application data."""

from django.contrib.auth.models import AnonymousUser
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from apps.jobs.models import ApplicationNote, JobApplication


def application_queryset_for_user(user) -> QuerySet[JobApplication]:
    """Return job applications owned by the supplied authenticated user."""
    if (
        isinstance(user, AnonymousUser)
        or not user.is_authenticated
        or not getattr(user, "pk", None)
    ):
        return JobApplication.objects.none()

    return JobApplication.objects.filter(owner=user).order_by(
        "-updated_at",
        "-created_at",
    )


def get_user_application_or_404(user, pk: int) -> JobApplication:
    """Return a user-owned application or raise a 404."""
    return get_object_or_404(application_queryset_for_user(user), pk=pk)


def get_recent_applications_for_user(
    user,
    limit: int = 5,
) -> QuerySet[JobApplication]:
    """Return recent user-owned applications in deterministic order."""
    return application_queryset_for_user(user)[:limit]


def notes_queryset_for_user(user) -> QuerySet[ApplicationNote]:
    """Return notes attached to the supplied user's applications."""
    if (
        isinstance(user, AnonymousUser)
        or not user.is_authenticated
        or not getattr(user, "pk", None)
    ):
        return ApplicationNote.objects.none()

    return ApplicationNote.objects.filter(application__owner=user).order_by(
        "-created_at"
    )


def get_note_count_for_user(user) -> int:
    """Return the number of notes attached to the supplied user's applications."""
    return notes_queryset_for_user(user).count()
