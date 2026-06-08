"""Factory helpers for insight tests."""

import factory

from apps.insights.models import JobInsight, TargetRoleProfile
from apps.jobs.factories import JobApplicationFactory
from apps.users.factories import UserFactory


class TargetRoleProfileFactory(factory.django.DjangoModelFactory):
    """Create a valid target role profile for tests."""

    class Meta:
        """Factory metadata for TargetRoleProfileFactory."""

        model = TargetRoleProfile

    owner = factory.SubFactory(UserFactory)
    title = "Graduate Backend Engineer"
    description = "Python, Django, APIs, PostgreSQL, Docker, and testing."
    keywords = ["python", "django", "api", "postgresql", "docker", "testing"]
    is_active = True


class JobInsightFactory(factory.django.DjangoModelFactory):
    """Create a valid stored job insight for tests."""

    class Meta:
        """Factory metadata for JobInsightFactory."""

        model = JobInsight

    job_application = factory.SubFactory(JobApplicationFactory)
    target_profile = factory.LazyAttribute(
        lambda obj: TargetRoleProfileFactory(owner=obj.job_application.owner)
    )
    source_hash = factory.Sequence(lambda number: f"{number:064x}"[-64:])
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
