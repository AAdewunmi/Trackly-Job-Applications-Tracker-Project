"""Integration tests for application list and create views."""

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.jobs.factories import JobApplicationFactory
from apps.jobs.models import JobApplication
from apps.users.factories import UserFactory


def valid_application_data(**overrides: object) -> dict[str, object]:
    """Return valid POST data for creating a job application."""
    data = {
        "title": "Backend Engineer",
        "company": "Example Ltd",
        "status": JobApplication.Status.APPLIED,
        "job_link": "https://example.com/jobs/backend-engineer",
        "applied_date": timezone.localdate().isoformat(),
        "job_description": "Build Django services and maintain APIs.",
        "notes": "Applied through the company careers page.",
    }
    data.update(overrides)
    return data


@pytest.mark.django_db
def test_application_list_requires_authentication(client) -> None:
    """Anonymous users should be redirected away from the list page."""
    response = client.get(reverse("jobs:application_list"))

    assert response.status_code == 302


@pytest.mark.django_db
def test_application_list_renders_empty_state(client) -> None:
    """Authenticated users with no applications should see an empty state."""
    user = UserFactory()
    client.force_login(user)

    response = client.get(reverse("jobs:application_list"))

    assert response.status_code == 200
    assert b"No job applications yet" in response.content


@pytest.mark.django_db
def test_application_list_shows_only_current_user_records(client) -> None:
    """The list page should not expose another user's applications."""
    user = UserFactory()
    other_user = UserFactory()
    own_application = JobApplicationFactory(owner=user, title="Own Role")
    JobApplicationFactory(owner=other_user, title="Other Role")
    client.force_login(user)

    response = client.get(reverse("jobs:application_list"))

    assert response.status_code == 200
    assert own_application.title.encode() in response.content
    assert b"Other Role" not in response.content


@pytest.mark.django_db
def test_application_create_requires_authentication(client) -> None:
    """Anonymous users should be redirected away from the create page."""
    response = client.get(reverse("jobs:application_create"))

    assert response.status_code == 302


@pytest.mark.django_db
def test_application_create_renders_form_for_authenticated_user(client) -> None:
    """Authenticated users should receive a create form defaulting to saved."""
    user = UserFactory()
    client.force_login(user)

    response = client.get(reverse("jobs:application_create"))

    assert response.status_code == 200
    assert b"Add job application" in response.content
    assert b'value="saved" selected' in response.content


@pytest.mark.django_db
def test_application_create_persists_application_for_current_user(client) -> None:
    """Submitting valid application data should create a user-owned record."""
    user = UserFactory()
    client.force_login(user)

    response = client.post(
        reverse("jobs:application_create"),
        data=valid_application_data(),
    )

    assert response.status_code == 302
    application = JobApplication.objects.get(owner=user)
    assert application.title == "Backend Engineer"
    assert application.company == "Example Ltd"


@pytest.mark.django_db
def test_application_create_rejects_invalid_future_date(client) -> None:
    """Invalid submitted data should re-render the form and avoid persistence."""
    user = UserFactory()
    client.force_login(user)
    future_date = timezone.localdate() + timedelta(days=1)

    response = client.post(
        reverse("jobs:application_create"),
        data=valid_application_data(applied_date=future_date.isoformat()),
    )

    assert response.status_code == 200
    assert JobApplication.objects.filter(owner=user).count() == 0
    assert b"Applied date cannot be in the future" in response.content


@pytest.mark.django_db
def test_application_create_sets_owner_from_request_user(client) -> None:
    """The owner should always come from the session, not posted form data."""
    user = UserFactory()
    other_user = UserFactory()
    client.force_login(user)

    client.post(
        reverse("jobs:application_create"),
        data={
            **valid_application_data(),
            "owner": other_user.pk,
        },
    )

    application = JobApplication.objects.get()
    assert application.owner == user


@pytest.mark.django_db
def test_application_detail_requires_authentication(client) -> None:
    """Anonymous users should be redirected away from application detail."""
    application = JobApplicationFactory()

    response = client.get(
        reverse("jobs:application_detail", kwargs={"pk": application.pk})
    )

    assert response.status_code == 302
    assert reverse("users:login") in response.url


@pytest.mark.django_db
def test_application_detail_renders_for_owner(client) -> None:
    """The owner should be able to view their application detail page."""
    user = UserFactory()
    application = JobApplicationFactory(owner=user, title="Product Analyst")
    client.force_login(user)

    response = client.get(
        reverse("jobs:application_detail", kwargs={"pk": application.pk})
    )

    assert response.status_code == 200
    assert response.context["application"] == application
    assert b"Product Analyst" in response.content


@pytest.mark.django_db
def test_application_detail_hides_other_users_records(client) -> None:
    """Users should receive a 404 for another user's application detail."""
    user = UserFactory()
    other_user = UserFactory()
    other_application = JobApplicationFactory(owner=other_user)
    client.force_login(user)

    response = client.get(
        reverse("jobs:application_detail", kwargs={"pk": other_application.pk})
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_application_update_hides_other_users_records(client) -> None:
    """Users should not be able to load another user's edit form."""
    user = UserFactory()
    other_user = UserFactory()
    other_application = JobApplicationFactory(owner=other_user)
    client.force_login(user)

    response = client.get(
        reverse("jobs:application_update", kwargs={"pk": other_application.pk})
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_application_update_post_hides_other_users_records(client) -> None:
    """Users should not be able to update another user's application."""
    user = UserFactory()
    other_user = UserFactory()
    other_application = JobApplicationFactory(
        owner=other_user,
        title="Original Role",
    )
    client.force_login(user)

    response = client.post(
        reverse("jobs:application_update", kwargs={"pk": other_application.pk}),
        data=valid_application_data(title="Changed Role"),
    )

    other_application.refresh_from_db()
    assert response.status_code == 404
    assert other_application.title == "Original Role"


@pytest.mark.django_db
def test_application_delete_hides_other_users_records(client) -> None:
    """Users should not be able to load another user's delete confirmation."""
    user = UserFactory()
    other_user = UserFactory()
    other_application = JobApplicationFactory(owner=other_user)
    client.force_login(user)

    response = client.get(
        reverse("jobs:application_delete", kwargs={"pk": other_application.pk})
    )

    assert response.status_code == 404
