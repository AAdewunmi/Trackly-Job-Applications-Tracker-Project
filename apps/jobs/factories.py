"""factory_boy factories for the jobs app."""

from datetime import timedelta

import factory
from django.utils import timezone

from apps.jobs.models import ApplicationNote
from apps.jobs.models import JobApplication
from apps.users.factories import UserFactory


class JobApplicationFactory(factory.django.DjangoModelFactory):
    """Factory for creating valid job application records in tests."""

    class Meta:
        """Factory metadata for the JobApplication model."""

        model = JobApplication

    owner = factory.SubFactory(UserFactory)
    title = factory.Sequence(lambda number: f"Backend Engineer {number}")
    company = factory.Sequence(lambda number: f"Company {number}")
    status = JobApplication.Status.SAVED
    job_link = factory.Sequence(
        lambda number: f"https://example.com/jobs/{number}"
    )
    applied_date = factory.LazyFunction(
        lambda: timezone.localdate() - timedelta(days=1)
    )
    job_description = (
        "Build Django services, work with PostgreSQL, and maintain tested APIs."
    )
    notes = "Initial application record created for test coverage."


class ApplicationNoteFactory(factory.django.DjangoModelFactory):
    """Factory for creating valid application notes in tests."""

    class Meta:
        """Factory metadata for the ApplicationNote model."""

        model = ApplicationNote

    application = factory.SubFactory(JobApplicationFactory)
    body = factory.Sequence(lambda number: f"Follow-up note {number}")
