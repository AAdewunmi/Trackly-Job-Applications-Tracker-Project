"""Model tests for Trackly job application tracking."""

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

from apps.jobs.models import ApplicationNote, JobApplication
from apps.users.factories import UserFactory


@pytest.mark.django_db
def test_job_application_string_and_absolute_url() -> None:
    """Job applications should expose readable labels and canonical URLs."""
    owner = UserFactory()
    application = JobApplication.objects.create(
        owner=owner,
        title="Product Analyst",
        company="Example Co",
    )

    assert str(application) == "Product Analyst at Example Co"
    assert application.get_absolute_url() == reverse(
        "jobs:application_detail",
        kwargs={"pk": application.pk},
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("field_name", "field_value", "message"),
    [
        ("title", " ", "Application title is required."),
        ("company", " ", "Company name is required."),
        ("status", "unknown", "Application status is not valid."),
        (
            "applied_date",
            timezone.localdate() + timezone.timedelta(days=1),
            "Applied date cannot be in the future.",
        ),
    ],
)
def test_job_application_validation(
    field_name: str,
    field_value: object,
    message: str,
) -> None:
    """Job applications should reject invalid domain values."""
    application = JobApplication(
        owner=UserFactory(),
        title="Product Analyst",
        company="Example Co",
    )
    setattr(application, field_name, field_value)

    with pytest.raises(ValidationError) as error:
        application.full_clean()

    assert message in str(error.value)


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
    application = JobApplication.objects.create(
        owner=owner,
        title="Data Analyst",
        company="Example Co",
    )
    note = ApplicationNote.objects.create(
        application=application,
        body="Send portfolio.",
    )

    assert note.owner == owner
    assert str(note) == "Note for Data Analyst at Example Co"


@pytest.mark.django_db
def test_application_note_requires_body() -> None:
    """Application notes should reject blank content."""
    application = JobApplication.objects.create(
        owner=UserFactory(),
        title="Data Analyst",
        company="Example Co",
    )
    note = ApplicationNote(application=application, body=" ")

    with pytest.raises(ValidationError, match="Note body is required."):
        note.save()
