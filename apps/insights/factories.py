"""
factory_boy factories for Trackly insight tests.
"""

import factory

from apps.insights.models import JobInsight, TargetRoleProfile
from apps.jobs.factories import JobApplicationFactory
from apps.users.factories import UserFactory


class TargetRoleProfileFactory(factory.django.DjangoModelFactory):
    """Factory for target role profiles."""

    class Meta:
        """Factory metadata for target role profiles."""

        model = TargetRoleProfile

    owner = factory.SubFactory(UserFactory)
    title = "Graduate Backend Engineer"
    description = "Python, Django, APIs, PostgreSQL, Docker, and testing."
    keywords = ["python", "django", "api", "postgresql", "docker", "testing"]
    is_active = True


class JobInsightFactory(factory.django.DjangoModelFactory):
    """Factory for stored job insights."""

    class Meta:
        """Factory metadata for job insights."""

        model = JobInsight

    job_application = factory.SubFactory(JobApplicationFactory)
    target_profile = factory.LazyAttribute(
        lambda obj: TargetRoleProfileFactory(owner=obj.job_application.owner)
    )
    source_hash = factory.Sequence(lambda n: f"{n:064d}"[-64:])
    pipeline_version = "nltk-tfidf-cosine-v1"
    clean_job_text = "python django api test"
    clean_target_text = "python django api postgresql docker test"
    extracted_terms = ["python", "django", "api", "test"]
    top_overlapping_terms = ["python", "django", "api", "test"]
    missing_target_terms = ["postgresql", "docker"]
    similarity_score = 0.67
    score_label = "Strong match"
    explanation = (
        "Strong match: this job description overlaps with your target profile on "
        "python, django, api, and test. Missing or weaker target terms include "
        "postgresql and docker."
    )
