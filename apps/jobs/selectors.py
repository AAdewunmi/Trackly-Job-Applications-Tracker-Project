"""Read query helpers for Trackly job application workflows."""

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from apps.jobs.models import JobApplication


def application_queryset_for_user(user) -> QuerySet[JobApplication]:
    """Return job applications owned by the provided user."""
    return JobApplication.objects.filter(owner=user)


def get_user_application_or_404(user, pk: int) -> JobApplication:
    """Return a user-owned application or raise a 404."""
    return get_object_or_404(application_queryset_for_user(user), pk=pk)
