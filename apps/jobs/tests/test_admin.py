"""Admin tests for Trackly job application models."""

import pytest
from django.contrib import admin

from apps.jobs.admin import ApplicationNoteAdmin
from apps.jobs.models import ApplicationNote, JobApplication
from apps.users.factories import UserFactory


@pytest.mark.django_db
def test_application_note_admin_owner_email() -> None:
    """Application note admin should expose the owning user's email."""
    owner = UserFactory(email="owner@example.com")
    application = JobApplication.objects.create(
        owner=owner,
        title="Product Analyst",
        company="Example Co",
    )
    note = ApplicationNote.objects.create(
        application=application,
        body="Follow up next week.",
    )
    model_admin = ApplicationNoteAdmin(ApplicationNote, admin.site)

    assert model_admin.owner_email(note) == "owner@example.com"
