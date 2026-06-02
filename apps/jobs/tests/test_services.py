"""Service tests for user-scoped job application metrics."""

import pytest
from django.contrib.auth.models import AnonymousUser

from apps.jobs.factories import ApplicationNoteFactory, JobApplicationFactory
from apps.jobs.models import JobApplication
from apps.jobs.services import (
    get_application_status_counts,
    get_user_pipeline_metrics,
)
from apps.users.factories import UserFactory


@pytest.mark.django_db
def test_application_status_counts_are_scoped_to_current_user() -> None:
    """Status counts should include every state and exclude other users."""
    owner = UserFactory(email="owner@example.com")
    other_user = UserFactory(email="other@example.com")
    JobApplicationFactory(owner=owner, status=JobApplication.Status.APPLIED)
    JobApplicationFactory(owner=owner, status=JobApplication.Status.INTERVIEWING)
    JobApplicationFactory(owner=other_user, status=JobApplication.Status.OFFER)

    counts = get_application_status_counts(owner)

    assert counts[JobApplication.Status.APPLIED] == 1
    assert counts[JobApplication.Status.INTERVIEWING] == 1
    assert counts[JobApplication.Status.OFFER] == 0
    assert set(counts) == set(JobApplication.Status.values)


@pytest.mark.django_db
def test_pipeline_metrics_are_scoped_to_current_user() -> None:
    """Pipeline metrics should summarize only the supplied user's records."""
    owner = UserFactory(email="owner@example.com")
    other_user = UserFactory(email="other@example.com")
    applied = JobApplicationFactory(
        owner=owner,
        status=JobApplication.Status.APPLIED,
    )
    JobApplicationFactory(owner=owner, status=JobApplication.Status.INTERVIEWING)
    JobApplicationFactory(owner=owner, status=JobApplication.Status.REJECTED)
    JobApplicationFactory(owner=other_user, status=JobApplication.Status.OFFER)
    ApplicationNoteFactory(application=applied)
    ApplicationNoteFactory(application=applied)

    metrics = get_user_pipeline_metrics(owner)

    assert metrics == {
        "total_applications": 3,
        "active_applications": 2,
        "interviews": 1,
        "offers": 0,
        "rejections": 1,
        "notes": 2,
    }


@pytest.mark.django_db
def test_pipeline_metrics_are_empty_for_anonymous_user() -> None:
    """Anonymous dashboard previews should receive empty pipeline metrics."""
    JobApplicationFactory()

    metrics = get_user_pipeline_metrics(AnonymousUser())

    assert metrics == {
        "total_applications": 0,
        "active_applications": 0,
        "interviews": 0,
        "offers": 0,
        "rejections": 0,
        "notes": 0,
    }
