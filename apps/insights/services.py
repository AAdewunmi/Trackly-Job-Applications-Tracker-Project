"""Business services for target-role job insight generation."""

from __future__ import annotations

import hashlib
import re

from django.core.exceptions import ValidationError

from apps.insights.models import JobInsight, TargetRoleProfile
from apps.jobs.models import JobApplication

PIPELINE_VERSION = "keyword-overlap-v1"
TOKEN_PATTERN = re.compile(r"[a-z0-9+#.]+")


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

    clean_job_text = _clean_text(
        job_application.title,
        job_application.company,
        job_application.job_description,
        job_application.notes,
    )
    clean_target_text = _clean_text(
        target_profile.title,
        target_profile.description,
        *target_profile.keywords,
    )
    job_terms = _ordered_terms(clean_job_text)
    target_terms = _ordered_terms(clean_target_text)
    overlapping_terms = [term for term in target_terms if term in set(job_terms)]
    missing_terms = [term for term in target_terms if term not in set(job_terms)]
    similarity_score = _similarity_score(job_terms, target_terms)
    score_label = _score_label(similarity_score)

    insight, _created = JobInsight.objects.update_or_create(
        job_application=job_application,
        target_profile=target_profile,
        source_hash=_source_hash(clean_job_text, clean_target_text),
        pipeline_version=PIPELINE_VERSION,
        defaults={
            "clean_job_text": clean_job_text,
            "clean_target_text": clean_target_text,
            "extracted_terms": job_terms,
            "top_overlapping_terms": overlapping_terms[:10],
            "missing_target_terms": missing_terms[:10],
            "similarity_score": similarity_score,
            "score_label": score_label,
            "explanation": _explanation(score_label, overlapping_terms, missing_terms),
        },
    )
    return insight


def _clean_text(*values: object) -> str:
    """Return normalized text for deterministic keyword matching."""
    return " ".join(
        token.strip(".")
        for value in values
        for token in TOKEN_PATTERN.findall(str(value).lower())
        if token.strip(".")
    )


def _ordered_terms(text: str) -> list[str]:
    """Return de-duplicated terms in first-seen order."""
    seen_terms: set[str] = set()
    terms: list[str] = []

    for term in text.split():
        if term not in seen_terms:
            terms.append(term)
            seen_terms.add(term)

    return terms


def _source_hash(clean_job_text: str, clean_target_text: str) -> str:
    """Return a stable source hash for an unchanged job/profile pair."""
    source = f"{PIPELINE_VERSION}\n{clean_job_text}\n{clean_target_text}"
    return hashlib.sha256(source.encode()).hexdigest()


def _similarity_score(job_terms: list[str], target_terms: list[str]) -> float:
    """Return a simple overlap score between job and target terms."""
    if not target_terms:
        return 0.0

    overlap = set(job_terms) & set(target_terms)
    return round(len(overlap) / len(set(target_terms)), 2)


def _score_label(score: float) -> str:
    """Return a human-readable label for the similarity score."""
    if score >= 0.7:
        return "Strong match"
    if score >= 0.4:
        return "Partial match"
    return "Low match"


def _explanation(
    score_label: str,
    overlapping_terms: list[str],
    missing_terms: list[str],
) -> str:
    """Return a concise explanation for the generated insight."""
    overlap = ", ".join(overlapping_terms[:5]) or "no target terms"
    missing = ", ".join(missing_terms[:5]) or "no major target terms"
    return (
        f"{score_label}: this job overlaps with your target profile on {overlap}. "
        f"Missing or weaker target terms include {missing}."
    )
