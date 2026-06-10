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
    pipeline_version = JobInsight.PipelineVersion.NLTK_TFIDF_COSINE_V1
    clean_job_text = "python django api test"
    clean_target_text = "python django api postgresql docker test"
    extracted_terms = ["python", "django", "api", "test"]
    top_overlapping_terms = ["python", "django", "api", "test"]
    top_overlapping_weighted_terms = [
        {
            "term": "python",
            "job_weight": 0.5,
            "target_weight": 0.4,
            "overlap_weight": 0.2,
        },
        {
            "term": "django",
            "job_weight": 0.4,
            "target_weight": 0.35,
            "overlap_weight": 0.14,
        },
    ]
    missing_target_terms = ["postgresql", "docker"]
    missing_weighted_target_terms = [
        {"term": "postgresql", "target_weight": 0.3},
        {"term": "docker", "target_weight": 0.25},
    ]
    similarity_score = 0.67
    score_label = "Strong match"
    explanation = (
        "Strong match: this job description overlaps with your target profile on "
        "python, django, api, and test. Missing or weaker target terms include "
        "postgresql and docker."
    )
