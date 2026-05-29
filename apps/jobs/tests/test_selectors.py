"""Selector tests for Trackly job application workflows."""

import pytest
from django.http import Http404

from apps.jobs.factories import JobApplicationFactory
from apps.jobs.selectors import (
    application_queryset_for_user,
    get_user_application_or_404,
)
from apps.users.factories import UserFactory


@pytest.mark.django_db
def test_application_queryset_for_user_returns_owned_applications() -> None:
    """Application querysets should be scoped to the provided user."""
    owner = UserFactory(email="owner@example.com")
    other_user = UserFactory(email="other@example.com")
    owned_application = JobApplicationFactory(owner=owner)
    JobApplicationFactory(owner=other_user)

    applications = application_queryset_for_user(owner)

    assert list(applications) == [owned_application]


@pytest.mark.django_db
def test_get_user_application_or_404_returns_owned_application() -> None:
    """Owned application lookups should return the matching object."""
    owner = UserFactory()
    application = JobApplicationFactory(owner=owner)

    assert get_user_application_or_404(owner, pk=application.pk) == application


@pytest.mark.django_db
def test_get_user_application_or_404_hides_other_users_application() -> None:
    """Other users' applications should behave as missing."""
    owner = UserFactory(email="owner@example.com")
    other_user = UserFactory(email="other@example.com")
    application = JobApplicationFactory(owner=owner)

    with pytest.raises(Http404):
        get_user_application_or_404(other_user, pk=application.pk)
