"""factory_boy factories for Trackly insight tests."""

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
    source_hash = "b92fe13d490816687079bd0fb2d20809b282c183869b37f465ace60c4e95eeaf"
    pipeline_version = JobInsight.PipelineVersion.NLTK_TFIDF_COSINE_V1
    clean_job_text = "python django api test"
    clean_target_text = "python django api postgresql docker test"
    extracted_terms = [
        "api test",
        "api",
        "django",
        "django api",
        "python",
        "python django",
        "test",
    ]
    top_overlapping_terms = [
        "api",
        "django",
        "django api",
        "python",
        "python django",
        "test",
    ]
    top_overlapping_weighted_terms = [
        {
            "term": "api",
            "job_weight": 0.3541,
            "target_weight": 0.251,
            "overlap_weight": 0.0889,
        },
        {
            "term": "django",
            "job_weight": 0.3541,
            "target_weight": 0.251,
            "overlap_weight": 0.0889,
        },
        {
            "term": "django api",
            "job_weight": 0.3541,
            "target_weight": 0.251,
            "overlap_weight": 0.0889,
        },
        {
            "term": "python",
            "job_weight": 0.3541,
            "target_weight": 0.251,
            "overlap_weight": 0.0889,
        },
        {
            "term": "python django",
            "job_weight": 0.3541,
            "target_weight": 0.251,
            "overlap_weight": 0.0889,
        },
        {
            "term": "test",
            "job_weight": 0.3541,
            "target_weight": 0.251,
            "overlap_weight": 0.0889,
        },
    ]
    missing_target_terms = [
        "api postgresql",
        "docker",
        "docker test",
        "postgresql",
        "postgresql docker",
    ]
    missing_weighted_target_terms = [
        {"term": "api postgresql", "target_weight": 0.3527},
        {"term": "docker", "target_weight": 0.3527},
        {"term": "docker test", "target_weight": 0.3527},
        {"term": "postgresql", "target_weight": 0.3527},
        {"term": "postgresql docker", "target_weight": 0.3527},
    ]
    similarity_score = 0.53
    score_label = "Strong match"
    explanation = (
        "Strong match: this job description overlaps with your target profile on "
        "api, django, django api, python, python django, test. Missing or weaker "
        "target terms include api postgresql, docker, docker test, postgresql, "
        "postgresql docker."
    )
