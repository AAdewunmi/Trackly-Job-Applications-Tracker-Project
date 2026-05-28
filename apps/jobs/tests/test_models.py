"""Model tests for the jobs app."""

from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

from apps.jobs.factories import ApplicationNoteFactory, JobApplicationFactory
from apps.jobs.models import ApplicationNote, JobApplication
from apps.users.factories import UserFactory


@pytest.mark.django_db
def test_job_application_has_readable_string_representation() -> None:
    """A job application should render as role title at company."""
    application = JobApplicationFactory(
        title="Python Developer",
        company="Example Ltd",
    )

    assert str(application) == "Python Developer at Example Ltd"


@pytest.mark.django_db
def test_job_application_is_linked_to_owner() -> None:
    """A job application should belong to one authenticated user."""
    user = UserFactory()
    application = JobApplicationFactory(owner=user)

    assert application.owner == user


@pytest.mark.django_db
def test_job_application_has_absolute_url() -> None:
    """A job application should expose its canonical detail URL."""
    application = JobApplicationFactory()

    assert application.get_absolute_url() == reverse(
        "jobs:application_detail",
        kwargs={"pk": application.pk},
    )


@pytest.mark.django_db
def test_job_application_rejects_invalid_status() -> None:
    """An application should reject statuses outside the defined workflow."""
    with pytest.raises(ValidationError, match="Application status is not valid."):
        JobApplicationFactory(status="not-a-real-status")


@pytest.mark.django_db
def test_job_application_rejects_future_applied_date() -> None:
    """An application should not allow applied dates in the future."""
    future_date = timezone.localdate() + timedelta(days=1)

    with pytest.raises(ValidationError, match="Applied date cannot be in the future."):
        JobApplicationFactory(applied_date=future_date)


@pytest.mark.django_db
def test_job_application_rejects_blank_title() -> None:
    """An application should require a meaningful title."""
    with pytest.raises(ValidationError, match="Application title is required."):
        JobApplicationFactory(title="   ")


@pytest.mark.django_db
def test_job_application_rejects_blank_company() -> None:
    """An application should require a meaningful company name."""
    with pytest.raises(ValidationError, match="Company name is required."):
        JobApplicationFactory(company="   ")


@pytest.mark.django_db
def test_job_application_save_runs_validation() -> None:
    """Saving a job application should run model validation first."""
    application = JobApplication(
        owner=UserFactory(),
        title=" ",
        company="Example Co",
    )

    with pytest.raises(ValidationError, match="Application title is required."):
        application.save()


@pytest.mark.django_db
def test_application_note_owner_and_string() -> None:
    """Application notes should expose parent ownership and readable labels."""
    owner = UserFactory()
    application = JobApplicationFactory(
        owner=owner,
        title="Data Analyst",
        company="Example Co",
    )
    note = ApplicationNoteFactory(
        application=application,
        body="Send portfolio.",
    )

    assert note.owner == owner
    assert str(note) == "Note for Data Analyst at Example Co"


@pytest.mark.django_db
def test_application_note_requires_body() -> None:
    """Application notes should reject blank content."""
    application = JobApplicationFactory(
        owner=UserFactory(),
        title="Data Analyst",
        company="Example Co",
    )
    note = ApplicationNote(application=application, body=" ")

    with pytest.raises(ValidationError, match="Note body is required."):
        note.save()
