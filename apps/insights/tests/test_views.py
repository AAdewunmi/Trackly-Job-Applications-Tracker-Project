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
    insight = JobInsightFactory(
        job_application__owner=user,
        target_profile=profile,
        similarity_score=0.53,
        score_label="Strong match",
    )
    TargetRoleProfileFactory(owner=other_user, title="Foreign Target")
    JobInsightFactory(job_application__owner=other_user)
    client.force_login(user)

    response = client.get(reverse("insights:insight-list"))

    assert response.status_code == 200
    assert b"Backend Target" in response.content
    assert insight.job_application.title.encode() in response.content
    assert b"Foreign Target" not in response.content
    assert b"Insight score histogram" in response.content
    assert b"Target profile comparison" in response.content
    score_histogram = {
        bucket.label: bucket.count for bucket in response.context["score_histogram"]
    }
    assert score_histogram["Strong match"] == 1
    assert [
        summary.title for summary in response.context["target_profile_match_summaries"]
    ] == ["Backend Target"]
    assert response.context["target_profile_match_summaries"][0].average_score == 0.53


@pytest.mark.django_db
def test_insight_list_renders_filter_and_sort_controls(client) -> None:
    """The insight workspace should expose browser filters and sorting."""
    user = UserFactory()
    profile = TargetRoleProfileFactory(owner=user, title="Backend Target")
    JobInsightFactory(
        job_application__owner=user,
        target_profile=profile,
        score_label="Strong match",
    )
    client.force_login(user)

    response = client.get(reverse("insights:insight-list"))

    assert response.status_code == 200
    assert b"Insight workspace" in response.content
    assert b'name="target_profile"' in response.content
    assert b'name="score_label"' in response.content
    assert b'name="sort"' in response.content
    assert b"Highest score" in response.content
    assert b"Strong match" in response.content
    assert b"Match quality visualisations" in response.content


@pytest.mark.django_db
def test_insight_list_renders_dashboard_generation_form(client) -> None:
    """The insights dashboard should expose direct insight generation."""
    user = UserFactory()
    application = JobApplicationFactory(owner=user, title="Backend Engineer")
    profile = TargetRoleProfileFactory(owner=user, title="Backend Target")
    client.force_login(user)

    response = client.get(reverse("insights:insight-list"))

    form = response.context["insight_generation_form"]
    assert response.status_code == 200
    assert list(form.fields["application"].queryset) == [application]
    assert list(form.fields["target_profile"].queryset) == [profile]
    assert b"Create a retrieval-style match" in response.content
    assert reverse("insights:dashboard-job-insight-generate").encode() in (
        response.content
    )


@pytest.mark.django_db
def test_insight_list_generation_panel_renders_empty_states(client) -> None:
    """Missing setup records should produce useful dashboard generation actions."""
    user = UserFactory()
    client.force_login(user)

    response = client.get(reverse("insights:insight-list"))

    assert response.status_code == 200
    assert b"Add an application before generating dashboard insights." in (
        response.content
    )
    assert (
        b"Create an active target role profile before generating dashboard insights."
        in (response.content)
    )
    assert reverse("jobs:application_create").encode() in response.content
    assert reverse("insights:target-profile-create").encode() in response.content


@pytest.mark.django_db
def test_insight_list_filters_by_target_profile_and_score_label(client) -> None:
    """Filtering should narrow the visible insight list."""
    user = UserFactory()
    backend_profile = TargetRoleProfileFactory(owner=user, title="Backend Target")
    data_profile = TargetRoleProfileFactory(owner=user, title="Data Target")
    backend_insight = JobInsightFactory(
        job_application__owner=user,
        job_application__title="Backend Engineer",
        target_profile=backend_profile,
        score_label="Strong match",
    )
    JobInsightFactory(
        job_application__owner=user,
        job_application__title="Data Analyst",
        target_profile=data_profile,
        score_label="Developing match",
    )
    client.force_login(user)

    response = client.get(
        reverse("insights:insight-list"),
        {
            "target_profile": str(backend_profile.pk),
            "score_label": "Strong match",
        },
    )

    assert response.status_code == 200
    assert list(response.context["recent_insights"]) == [backend_insight]
    assert b"Backend Engineer" in response.content
    assert response.context["has_active_filters"] is True


@pytest.mark.django_db
def test_insight_list_sorts_by_highest_score(client) -> None:
    """Sorting by score should put the strongest match first."""
    user = UserFactory()
    lower_score = JobInsightFactory(
        job_application__owner=user,
        job_application__title="Lower Match",
        similarity_score=0.21,
    )
    higher_score = JobInsightFactory(
        job_application__owner=user,
        job_application__title="Higher Match",
        similarity_score=0.88,
    )
    client.force_login(user)

    response = client.get(
        reverse("insights:insight-list"),
        {"sort": "score_desc"},
    )

    assert response.status_code == 200
    assert list(response.context["recent_insights"]) == [higher_score, lower_score]
    assert response.content.find(b"Higher Match") < response.content.find(
        b"Lower Match"
    )


@pytest.mark.django_db
def test_insight_list_renders_filtered_empty_state(client) -> None:
    """No-match filter results should give users clear recovery actions."""
    user = UserFactory()
    profile = TargetRoleProfileFactory(owner=user, title="Backend Target")
    JobInsightFactory(
        job_application__owner=user,
        target_profile=profile,
        score_label="Strong match",
    )
    client.force_login(user)

    response = client.get(
        reverse("insights:insight-list"),
        {"target_profile": str(profile.pk), "score_label": "Developing match"},
    )

    assert response.status_code == 200
    assert list(response.context["recent_insights"]) == []
    assert b"No insights match these filters" in response.content
    assert reverse("insights:insight-list").encode() in response.content


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
def test_dashboard_generate_job_insight_creates_insight_and_redirects(client) -> None:
    """Generating from the insights dashboard should create a stored insight."""
    user = UserFactory()
    application = JobApplicationFactory(
        owner=user,
        job_description="Build Python Django APIs with PostgreSQL.",
    )
    profile = TargetRoleProfileFactory(
        owner=user,
        keywords=["python", "django", "api", "postgresql"],
    )
    client.force_login(user)

    response = client.post(
        reverse("insights:dashboard-job-insight-generate"),
        data={
            "application": application.pk,
            "target_profile": profile.pk,
        },
    )

    assert response.status_code == 302
    assert response["Location"] == reverse("insights:insight-list")
    assert JobInsight.objects.filter(
        job_application=application,
        target_profile=profile,
    ).exists()


@pytest.mark.django_db
def test_dashboard_generate_job_insight_rejects_foreign_records(client) -> None:
    """Dashboard generation should only accept the logged-in user's records."""
    user = UserFactory()
    other_user = UserFactory()
    foreign_application = JobApplicationFactory(owner=other_user)
    foreign_profile = TargetRoleProfileFactory(owner=other_user)
    client.force_login(user)

    response = client.post(
        reverse("insights:dashboard-job-insight-generate"),
        data={
            "application": foreign_application.pk,
            "target_profile": foreign_profile.pk,
        },
    )

    assert response.status_code == 302
    assert response["Location"] == reverse("insights:insight-list")
    assert JobInsight.objects.count() == 0


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
