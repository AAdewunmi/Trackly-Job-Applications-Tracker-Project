"""View tests for Trackly insight browser workflows."""

import pytest
from django.urls import reverse

from apps.insights.factories import JobInsightFactory, TargetRoleProfileFactory
from apps.insights.models import JobInsight, TargetRoleProfile
from apps.jobs.factories import JobApplicationFactory
from apps.users.factories import UserFactory


@pytest.mark.django_db
def test_insight_list_requires_authentication(client) -> None:
    """Anonymous users should be redirected from the insight list."""
    response = client.get(reverse("insights:insight-list"))

    assert response.status_code == 302
    assert reverse("users:login") in response.url


@pytest.mark.django_db
def test_insight_list_renders_user_scoped_profiles_and_insights(client) -> None:
    """Insight list should render only records owned by the current user."""
    user = UserFactory()
    other_user = UserFactory()
    profile = TargetRoleProfileFactory(owner=user, title="Backend Target")
    insight = JobInsightFactory(job_application__owner=user, target_profile=profile)
    TargetRoleProfileFactory(owner=other_user, title="Foreign Target")
    JobInsightFactory(job_application__owner=other_user)
    client.force_login(user)

    response = client.get(reverse("insights:insight-list"))

    assert response.status_code == 200
    assert b"Backend Target" in response.content
    assert insight.job_application.title.encode() in response.content
    assert b"Foreign Target" not in response.content


@pytest.mark.django_db
def test_target_profile_create_renders_form(client) -> None:
    """Authenticated users should be able to load the target profile form."""
    user = UserFactory()
    client.force_login(user)

    response = client.get(reverse("insights:target-profile-create"))

    assert response.status_code == 200
    assert b"Create target profile" in response.content


@pytest.mark.django_db
def test_target_profile_create_normalises_keywords_and_redirects(client) -> None:
    """Posting the target profile form should store normalised keyword JSON."""
    user = UserFactory()
    client.force_login(user)

    response = client.post(
        reverse("insights:target-profile-create"),
        data={
            "title": "Backend Target",
            "description": "Python and Django backend role.",
            "keywords_text": "Python, Django, API, Python",
            "is_active": "on",
        },
    )

    profile = TargetRoleProfile.objects.get(owner=user)

    assert response.status_code == 302
    assert response["Location"] == reverse("insights:insight-list")
    assert profile.keywords == ["python", "django", "api"]


@pytest.mark.django_db
def test_generate_job_insight_creates_insight_and_redirects(client) -> None:
    """Generating an insight from application detail should create a record."""
    user = UserFactory()
    application = JobApplicationFactory(owner=user)
    profile = TargetRoleProfileFactory(owner=user)
    client.force_login(user)

    response = client.post(
        reverse(
            "insights:job-insight-generate",
            kwargs={"application_pk": application.pk},
        ),
        data={"target_profile": profile.pk},
    )

    assert response.status_code == 302
    assert response["Location"] == application.get_absolute_url()
    assert JobInsight.objects.filter(
        job_application=application,
        target_profile=profile,
    ).exists()
