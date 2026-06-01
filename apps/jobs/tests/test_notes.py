"""Tests for application notes and note ownership behaviour."""

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from apps.jobs.factories import ApplicationNoteFactory, JobApplicationFactory
from apps.jobs.models import ApplicationNote
from apps.users.factories import UserFactory


@pytest.mark.django_db
def test_owner_can_add_note_to_application_detail(client) -> None:
    """Posting a valid note on the detail page should persist it."""
    user = UserFactory()
    application = JobApplicationFactory(owner=user)
    client.force_login(user)

    response = client.post(
        reverse("jobs:application_detail", kwargs={"pk": application.pk}),
        data={"body": "Recruiter replied and asked for availability."},
    )

    assert response.status_code == 302
    note = ApplicationNote.objects.get(application=application)
    assert note.body == "Recruiter replied and asked for availability."


@pytest.mark.django_db
def test_blank_note_is_rejected(client) -> None:
    """Blank notes should not be persisted."""
    user = UserFactory()
    application = JobApplicationFactory(owner=user)
    client.force_login(user)

    response = client.post(
        reverse("jobs:application_detail", kwargs={"pk": application.pk}),
        data={"body": "   "},
    )

    assert response.status_code == 200
    assert ApplicationNote.objects.filter(application=application).count() == 0
    assert b"Note body is required" in response.content


@pytest.mark.django_db
def test_notes_render_on_application_detail(client) -> None:
    """Existing notes should appear on the application detail page."""
    user = UserFactory()
    application = JobApplicationFactory(owner=user)
    note = ApplicationNoteFactory(
        application=application,
        body="Interview scheduled for Thursday.",
    )
    client.force_login(user)

    response = client.get(
        reverse("jobs:application_detail", kwargs={"pk": application.pk})
    )

    assert response.status_code == 200
    assert note.body.encode() in response.content


@pytest.mark.django_db
def test_user_cannot_add_note_to_another_users_application(client) -> None:
    """Foreign application access should fail before note creation."""
    user = UserFactory()
    other_user = UserFactory()
    application = JobApplicationFactory(owner=other_user)
    client.force_login(user)

    response = client.post(
        reverse("jobs:application_detail", kwargs={"pk": application.pk}),
        data={"body": "Attempted foreign note."},
    )

    assert response.status_code == 404
    assert ApplicationNote.objects.count() == 0


@pytest.mark.django_db
def test_application_note_owner_is_derived_from_application() -> None:
    """A note should expose its owner through the parent application."""
    user = UserFactory()
    application = JobApplicationFactory(owner=user)
    note = ApplicationNoteFactory(application=application)

    assert note.owner == user


@pytest.mark.django_db
def test_application_note_rejects_blank_body() -> None:
    """The note model should reject empty note bodies."""
    application = JobApplicationFactory()

    with pytest.raises(ValidationError):
        ApplicationNoteFactory(application=application, body="   ")
