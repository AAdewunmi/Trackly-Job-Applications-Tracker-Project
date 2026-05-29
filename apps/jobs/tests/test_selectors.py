"""Selector tests for user-scoped job application queries."""

from datetime import timedelta

import pytest
from django.contrib.auth.models import AnonymousUser
from django.http import Http404
from django.utils import timezone

from apps.jobs.factories import ApplicationNoteFactory, JobApplicationFactory
from apps.jobs.selectors import (
    application_queryset_for_user,
    get_note_count_for_user,
    get_recent_applications_for_user,
    get_user_application_or_404,
    notes_queryset_for_user,
)
from apps.users.factories import UserFactory


def set_application_updated_at(application, updated_at) -> None:
    """Set an application timestamp after factory save hooks run."""
    type(application).objects.filter(pk=application.pk).update(updated_at=updated_at)
    application.refresh_from_db()


def set_note_created_at(note, created_at) -> None:
    """Set a note timestamp after factory save hooks run."""
    type(note).objects.filter(pk=note.pk).update(created_at=created_at)
    note.refresh_from_db()


@pytest.mark.django_db
def test_application_queryset_returns_only_current_user_records() -> None:
    """The application selector should isolate records by owner."""
    owner = UserFactory(email="owner@example.com")
    other_user = UserFactory(email="other@example.com")
    first_application = JobApplicationFactory(owner=owner)
    second_application = JobApplicationFactory(owner=owner)
    JobApplicationFactory(owner=other_user)
    now = timezone.now()
    set_application_updated_at(first_application, now - timedelta(days=1))
    set_application_updated_at(second_application, now)

    applications = application_queryset_for_user(owner)

    assert list(applications) == [second_application, first_application]


@pytest.mark.django_db
def test_application_queryset_for_user_returns_none_for_anonymous_user() -> None:
    """Anonymous users should not receive any applications."""
    JobApplicationFactory()

    applications = application_queryset_for_user(AnonymousUser())

    assert list(applications) == []


@pytest.mark.django_db
def test_application_queryset_returns_empty_for_unsaved_user(
    django_user_model,
) -> None:
    """Unsaved user-like objects should not leak application records."""
    JobApplicationFactory()
    unsaved_user = django_user_model()

    applications = application_queryset_for_user(unsaved_user)

    assert applications.count() == 0


@pytest.mark.django_db
def test_get_user_application_or_404_returns_owned_application() -> None:
    """Owned application lookups should return the matching object."""
    owner = UserFactory()
    application = JobApplicationFactory(owner=owner)

    assert get_user_application_or_404(owner, pk=application.pk) == application


@pytest.mark.django_db
def test_get_user_application_or_404_hides_other_users_application() -> None:
    """Other users' applications should behave as missing."""
    owner = UserFactory(email="owner@example.com")
    other_user = UserFactory(email="other@example.com")
    application = JobApplicationFactory(owner=owner)

    with pytest.raises(Http404):
        get_user_application_or_404(other_user, pk=application.pk)


@pytest.mark.django_db
def test_recent_applications_respects_limit() -> None:
    """Recent application selector should return the requested number."""
    owner = UserFactory()
    first_application = JobApplicationFactory(owner=owner)
    second_application = JobApplicationFactory(owner=owner)
    third_application = JobApplicationFactory(owner=owner)
    now = timezone.now()
    set_application_updated_at(first_application, now - timedelta(days=2))
    set_application_updated_at(second_application, now - timedelta(days=1))
    set_application_updated_at(third_application, now)

    applications = get_recent_applications_for_user(owner, limit=2)

    assert list(applications) == [third_application, second_application]
    assert first_application not in applications


@pytest.mark.django_db
def test_notes_queryset_for_user_returns_owned_notes() -> None:
    """Note querysets should be scoped through application ownership."""
    owner = UserFactory(email="owner@example.com")
    other_user = UserFactory(email="other@example.com")
    owner_application = JobApplicationFactory(owner=owner)
    other_application = JobApplicationFactory(owner=other_user)
    first_note = ApplicationNoteFactory(application=owner_application)
    second_note = ApplicationNoteFactory(application=owner_application)
    ApplicationNoteFactory(application=other_application)
    now = timezone.now()
    set_note_created_at(first_note, now - timedelta(days=1))
    set_note_created_at(second_note, now)

    notes = notes_queryset_for_user(owner)

    assert list(notes) == [second_note, first_note]


@pytest.mark.django_db
def test_notes_queryset_for_user_returns_none_for_anonymous_user() -> None:
    """Anonymous users should not receive any application notes."""
    ApplicationNoteFactory()

    notes = notes_queryset_for_user(AnonymousUser())

    assert list(notes) == []


@pytest.mark.django_db
def test_note_count_is_scoped_to_current_user() -> None:
    """Note counts should only include notes on the user's applications."""
    owner = UserFactory(email="owner@example.com")
    other_user = UserFactory(email="other@example.com")
    owner_application = JobApplicationFactory(owner=owner)
    other_application = JobApplicationFactory(owner=other_user)
    ApplicationNoteFactory(application=owner_application)
    ApplicationNoteFactory(application=owner_application)
    ApplicationNoteFactory(application=other_application)

    assert get_note_count_for_user(owner) == 2
