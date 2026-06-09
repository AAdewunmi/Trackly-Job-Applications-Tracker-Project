"""Business services for target-role job insight generation."""

from __future__ import annotations

import hashlib

from django.core.exceptions import ValidationError

from apps.insights.models import JobInsight, TargetRoleProfile
from apps.insights.nlp import (
    analyse_text_similarity,
    build_target_profile_text,
    preprocess_text,
)
from apps.jobs.models import JobApplication

PIPELINE_VERSION = JobInsight.PipelineVersion.NLTK_TFIDF_COSINE_V1


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
    job_application: JobApplication,
    target_profile: TargetRoleProfile | None = None,
) -> JobInsight:
    """Generate and store a user-scoped job insight for a target role profile."""
    target_profile = target_profile or get_active_target_profile(job_application.owner)
    if target_profile is None or not target_profile.is_active:
        raise TargetRoleProfileRequired(
            "An active target role profile is required before matching jobs."
        )

    if job_application.owner_id != target_profile.owner_id:
        raise ValidationError(
            "Job insight application and target profile must share an owner."
        )

    analysis = analyse_text_similarity(
        job_text=build_job_source_text(job_application),
        target_text=build_target_source_text(target_profile),
    )

    insight, _created = JobInsight.objects.update_or_create(
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
            "missing_target_terms": analysis.missing_target_terms,
            "similarity_score": analysis.similarity_score,
            "score_label": analysis.score_label,
            "explanation": analysis.explanation,
        },
    )
    return insight


def _clean_text(*values: object) -> str:
    """Return NLTK-standardised text for deterministic retrieval matching."""
    source_text = " ".join(str(value) for value in values if value)
    return preprocess_text(source_text)


def calculate_source_hash(
    *,
    clean_job_text: str,
    clean_target_text: str,
    pipeline_version: str = PIPELINE_VERSION,
) -> str:
    """Return a stable hash for cleaned job text, target text, and pipeline."""
    source = f"{pipeline_version}\n{clean_job_text}\n{clean_target_text}"
    return hashlib.sha256(source.encode()).hexdigest()


def _source_hash(clean_job_text: str, clean_target_text: str) -> str:
    """Return a stable source hash for an unchanged job/profile pair."""
    return calculate_source_hash(
        clean_job_text=clean_job_text,
        clean_target_text=clean_target_text,
    )
