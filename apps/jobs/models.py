"""Domain models for Trackly job application tracking."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone


class JobApplication(models.Model):
    """A user-owned job application tracked inside Trackly."""

    class Status(models.TextChoices):
        """Allowed workflow states for a tracked job application."""

        SAVED = "saved", "Saved"
        APPLIED = "applied", "Applied"
        SCREENING = "screening", "Screening"
        INTERVIEWING = "interviewing", "Interviewing"
        OFFER = "offer", "Offer"
        REJECTED = "rejected", "Rejected"
        WITHDRAWN = "withdrawn", "Withdrawn"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="job_applications",
    )
    title = models.CharField(max_length=160)
    company = models.CharField(max_length=160)
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.SAVED,
    )
    job_link = models.URLField(blank=True)
    applied_date = models.DateField(blank=True, null=True)
    job_description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Model metadata for deterministic application ordering."""

        ordering = ["-updated_at", "-created_at"]
        indexes = [
            models.Index(fields=["owner", "status"]),
            models.Index(fields=["owner", "-updated_at"]),
        ]

    def __str__(self) -> str:
        """Return a readable label for admin, logs, and tests."""
        return f"{self.title} at {self.company}"

    def clean(self) -> None:
        """Validate domain constraints before persistence."""
        super().clean()

        if not self.title or not self.title.strip():
            raise ValidationError({"title": "Application title is required."})

        if not self.company or not self.company.strip():
            raise ValidationError({"company": "Company name is required."})

        if self.status not in self.Status.values:
            raise ValidationError({"status": "Application status is not valid."})

        if self.applied_date and self.applied_date > timezone.localdate():
            raise ValidationError(
                {"applied_date": "Applied date cannot be in the future."}
            )

    def save(self, *args: object, **kwargs: object) -> None:
        """Persist the application after running model validation."""
        self.full_clean()
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        """Return the canonical detail URL for this job application."""
        return reverse("jobs:application_detail", kwargs={"pk": self.pk})


class ApplicationNote(models.Model):
    """A user-owned note attached to a job application through its parent."""

    application = models.ForeignKey(
        JobApplication,
        on_delete=models.CASCADE,
        related_name="application_notes",
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Model metadata for deterministic note ordering."""

        ordering = ["-created_at"]

    def __str__(self) -> str:
        """Return a readable note label."""
        return f"Note for {self.application}"

    @property
    def owner(self):
        """Return the note owner through the parent application."""
        return self.application.owner

    def clean(self) -> None:
        """Validate note content before persistence."""
        super().clean()

        if not self.body or not self.body.strip():
            raise ValidationError({"body": "Note body is required."})

    def save(self, *args: object, **kwargs: object) -> None:
        """Persist the note after running model validation."""
        self.full_clean()
        super().save(*args, **kwargs)