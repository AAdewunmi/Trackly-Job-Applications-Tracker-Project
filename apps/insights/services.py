"""
Business services for target-role job insight generation.

Insight creation should go through generate_job_insight() so preprocessing,
vectorisation, scoring, hashing, explanation, and persistence rules stay in one
place. Callers should not create JobInsight records directly.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from django.core.exceptions import PermissionDenied, ValidationError

from apps.insights.models import JobInsight, TargetRoleProfile
from apps.insights.nlp import (
    analyse_text_similarity,
    build_target_profile_text,
    preprocess_text,
)
from apps.jobs.models import JobApplication

PIPELINE_VERSION = JobInsight.PipelineVersion.NLTK_TFIDF_COSINE_V1


@dataclass(frozen=True)
class InsightGenerationResult:
    """Return object for explicit user-scoped insight generation calls."""

    insight: JobInsight
    created: bool


class TargetRoleProfileRequired(Exception):
    """Raised when insight generation needs an active target role profile."""


def get_active_target_profile(user) -> TargetRoleProfile | None:
    """Return the most recently updated active target profile for a user."""
    if not getattr(user, "is_authenticated", False):
        return None

    return TargetRoleProfile.objects.filter(owner=user, is_active=True).first()


def can_generate_insight(user) -> bool:
    """Return whether the user has an active target role baseline."""
    return get_active_target_profile(user) is not None


def build_job_source_text(job_application: JobApplication) -> str:
    """Return the job-side source text used for insight generation."""
    parts = [
        job_application.title,
        job_application.company,
        job_application.job_description,
        job_application.notes,
    ]
    return "\n".join(str(part) for part in parts if part)


def build_target_source_text(target_profile: TargetRoleProfile) -> str:
    """Return the target-side source text used for insight generation."""
    return build_target_profile_text(
        title=target_profile.title,
        description=target_profile.description,
        keywords=target_profile.keywords,
    )


def generate_job_insight(
    job_application: JobApplication | None = None,
    target_profile: TargetRoleProfile | None = None,
    *,
    user=None,
    application: JobApplication | None = None,
) -> JobInsight | InsightGenerationResult:
    """Generate and store a user-scoped job insight for a target role profile."""
    return_result = user is not None or application is not None
    if application is not None:
        if job_application is not None and job_application != application:
            raise ValueError("Provide either job_application or application, not both.")
        job_application = application

    if job_application is None:
        raise ValueError("A job application is required to generate an insight.")

    if user is not None and job_application.owner_id != user.id:
        raise PermissionDenied(
            "Cannot generate insight for another user's application."
        )

    target_profile = target_profile or get_active_target_profile(job_application.owner)
    if target_profile is None or not target_profile.is_active:
        raise TargetRoleProfileRequired(
            "An active target role profile is required before matching jobs."
        )

    if user is not None and target_profile.owner_id != user.id:
        raise PermissionDenied("Cannot use another user's target role profile.")

    if job_application.owner_id != target_profile.owner_id:
        raise ValidationError(
            "Job insight application and target profile must share an owner."
        )

    analysis = analyse_text_similarity(
        job_text=build_job_source_text(job_application),
        target_text=build_target_source_text(target_profile),
    )

    insight, created = JobInsight.objects.update_or_create(
        job_application=job_application,
        target_profile=target_profile,
        source_hash=calculate_source_hash(
            clean_job_text=analysis.clean_job_text,
            clean_target_text=analysis.clean_target_text,
        ),
        pipeline_version=PIPELINE_VERSION,
        defaults={
            "clean_job_text": analysis.clean_job_text,
            "clean_target_text": analysis.clean_target_text,
            "extracted_terms": analysis.extracted_terms,
            "top_overlapping_terms": analysis.top_overlapping_terms,
            "top_overlapping_weighted_terms": analysis.top_overlapping_weighted_terms,
            "missing_target_terms": analysis.missing_target_terms,
            "missing_weighted_target_terms": analysis.missing_weighted_target_terms,
            "similarity_score": analysis.similarity_score,
            "score_label": analysis.score_label,
            "explanation": analysis.explanation,
        },
    )
    if return_result:
        return InsightGenerationResult(insight=insight, created=created)
    return insight


def _clean_text(*values: object) -> str:
    """Return NLTK-standardised text for deterministic retrieval matching."""
    source_text = " ".join(str(value) for value in values if value)
    return preprocess_text(source_text)


def calculate_source_hash(
    *,
    clean_job_text: str | None = None,
    clean_target_text: str | None = None,
    job_source_text: str | None = None,
    target_source_text: str | None = None,
    pipeline_version: str = PIPELINE_VERSION,
) -> str:
    """Return a stable hash for cleaned job text, target text, and pipeline."""
    if clean_job_text is None:
        clean_job_text = _clean_text(job_source_text)
    if clean_target_text is None:
        clean_target_text = _clean_text(target_source_text)

    source = f"{pipeline_version}\n{clean_job_text}\n{clean_target_text}"
    return hashlib.sha256(source.encode()).hexdigest()


def _source_hash(clean_job_text: str, clean_target_text: str) -> str:
    """Return a stable source hash for an unchanged job/profile pair."""
    return calculate_source_hash(
        clean_job_text=clean_job_text,
        clean_target_text=clean_target_text,
    )
