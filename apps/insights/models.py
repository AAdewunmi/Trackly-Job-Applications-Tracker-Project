"""
Persistence models for Trackly's retrieval-style job insight feature.
"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.jobs.models import JobApplication


class TargetRoleProfile(models.Model):
    """A user-owned target role profile used for job-fit matching."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="target_role_profiles",
    )
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    keywords = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Model metadata for target role profile query behaviour."""

        ordering = ["-updated_at", "-created_at"]

    def __str__(self) -> str:
        """Return a readable representation of the target role profile."""
        return self.title

    def clean(self) -> None:
        """Validate keyword structure for retrieval-style matching."""
        super().clean()
        if not isinstance(self.keywords, list):
            raise ValidationError({"keywords": "Keywords must be stored as a list."})

        cleaned_keywords = [
            str(keyword).strip()
            for keyword in self.keywords
            if str(keyword).strip()
        ]

        if not cleaned_keywords:
            raise ValidationError(
                {"keywords": "At least one target keyword is required."}
            )

    def save(self, *args, **kwargs):
        """Normalise keywords before saving the target profile."""
        if isinstance(self.keywords, list):
            seen_keywords: set[str] = set()
            normalised_keywords: list[str] = []

            for keyword in self.keywords:
                cleaned = str(keyword).strip().lower()
                if cleaned and cleaned not in seen_keywords:
                    normalised_keywords.append(cleaned)
                    seen_keywords.add(cleaned)

            self.keywords = normalised_keywords

        super().save(*args, **kwargs)


class JobInsight(models.Model):
    """Stored retrieval-style insight generated from a job application."""

    job_application = models.ForeignKey(
        JobApplication,
        on_delete=models.CASCADE,
        related_name="insights",
    )
    target_profile = models.ForeignKey(
        TargetRoleProfile,
        on_delete=models.CASCADE,
        related_name="job_insights",
    )
    source_hash = models.CharField(max_length=64)
    pipeline_version = models.CharField(max_length=80)
    clean_job_text = models.TextField(blank=True)
    clean_target_text = models.TextField(blank=True)
    extracted_terms = models.JSONField(default=list)
    top_overlapping_terms = models.JSONField(default=list)
    missing_target_terms = models.JSONField(default=list)
    similarity_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    score_label = models.CharField(max_length=40)
    explanation = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Model metadata for stored job insights."""

        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "job_application",
                    "target_profile",
                    "source_hash",
                    "pipeline_version",
                ],
                name="unique_insight_for_unchanged_retrieval_source",
            )
        ]

    def __str__(self) -> str:
        """Return a readable representation of the stored insight."""
        return f"Insight for {self.job_application}"

    def clean(self) -> None:
        """Validate insight ownership and JSON list fields."""
        super().clean()

        if (
            self.job_application_id
            and self.target_profile_id
            and self.job_application.owner_id != self.target_profile.owner_id
        ):
            raise ValidationError(
                "Job insight application and target profile must share an owner."
            )

        list_fields = {
            "extracted_terms": self.extracted_terms,
            "top_overlapping_terms": self.top_overlapping_terms,
            "missing_target_terms": self.missing_target_terms,
        }

        for field_name, value in list_fields.items():
            if not isinstance(value, list):
                raise ValidationError({field_name: "This field must be a list."})
