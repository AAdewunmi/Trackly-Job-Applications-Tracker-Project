"""Tests for application notes and note ownership behaviour."""

import pytest
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
    assert (
        reverse("jobs:note_update", kwargs={"pk": note.pk}).encode() in response.content
    )
    assert (
        reverse("jobs:note_delete", kwargs={"pk": note.pk}).encode() in response.content
    )


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
def test_owner_can_load_note_update_form(client) -> None:
    """Owners should be able to load the edit form for their notes."""
    user = UserFactory()
    application = JobApplicationFactory(owner=user)
    note = ApplicationNoteFactory(application=application, body="Original note.")
    client.force_login(user)

    response = client.get(reverse("jobs:note_update", kwargs={"pk": note.pk}))

    assert response.status_code == 200
    assert b"Edit note" in response.content
    assert b"Original note." in response.content


@pytest.mark.django_db
def test_owner_can_update_note(client) -> None:
    """Posting valid note data should update the owned note."""
    user = UserFactory()
    application = JobApplicationFactory(owner=user)
    note = ApplicationNoteFactory(application=application, body="Original note.")
    client.force_login(user)

    response = client.post(
        reverse("jobs:note_update", kwargs={"pk": note.pk}),
        data={"body": "Updated note."},
    )

    note.refresh_from_db()
    assert response.status_code == 302
    assert response.url == application.get_absolute_url()
    assert note.body == "Updated note."


@pytest.mark.django_db
def test_note_update_rejects_blank_body(client) -> None:
    """Blank note updates should be rejected."""
    user = UserFactory()
    application = JobApplicationFactory(owner=user)
    note = ApplicationNoteFactory(application=application, body="Original note.")
    client.force_login(user)

    response = client.post(
        reverse("jobs:note_update", kwargs={"pk": note.pk}),
        data={"body": "   "},
    )

    note.refresh_from_db()
    assert response.status_code == 200
    assert note.body == "Original note."
    assert b"Note body is required" in response.content


@pytest.mark.django_db
def test_user_cannot_update_another_users_note(client) -> None:
    """Users should not be able to update foreign notes."""
    user = UserFactory()
    application = JobApplicationFactory(owner=UserFactory())
    note = ApplicationNoteFactory(application=application, body="Original note.")
    client.force_login(user)

    response = client.post(
        reverse("jobs:note_update", kwargs={"pk": note.pk}),
        data={"body": "Attempted update."},
    )

    note.refresh_from_db()
    assert response.status_code == 404
    assert note.body == "Original note."


@pytest.mark.django_db
def test_owner_can_load_note_delete_confirmation(client) -> None:
    """Owners should be able to load note delete confirmation."""
    user = UserFactory()
    application = JobApplicationFactory(owner=user)
    note = ApplicationNoteFactory(application=application, body="Delete me.")
    client.force_login(user)

    response = client.get(reverse("jobs:note_delete", kwargs={"pk": note.pk}))

    assert response.status_code == 200
    assert b"Delete this note?" in response.content
    assert b"Delete me." in response.content


@pytest.mark.django_db
def test_owner_can_delete_note(client) -> None:
    """Posting to note delete should remove the owned note."""
    user = UserFactory()
    application = JobApplicationFactory(owner=user)
    note = ApplicationNoteFactory(application=application)
    client.force_login(user)

    response = client.post(reverse("jobs:note_delete", kwargs={"pk": note.pk}))

    assert response.status_code == 302
    assert response.url == application.get_absolute_url()
    assert not ApplicationNote.objects.filter(pk=note.pk).exists()


@pytest.mark.django_db
def test_user_cannot_delete_another_users_note(client) -> None:
    """Users should not be able to delete foreign notes."""
    user = UserFactory()
    application = JobApplicationFactory(owner=UserFactory())
    note = ApplicationNoteFactory(application=application)
    client.force_login(user)

    response = client.post(reverse("jobs:note_delete", kwargs={"pk": note.pk}))

    assert response.status_code == 404
    assert ApplicationNote.objects.filter(pk=note.pk).exists()
