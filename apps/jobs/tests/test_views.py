"""View tests for Trackly job application workflows."""

import pytest
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory
from django.urls import reverse

from apps.jobs.models import ApplicationNote, JobApplication
from apps.jobs.views import application_create
from apps.users.factories import UserFactory


def add_request_messages(request) -> None:
    """Attach session and message storage to a request factory request."""
    SessionMiddleware(lambda current_request: None).process_request(request)
    request.session.save()
    request._messages = FallbackStorage(request)


@pytest.mark.django_db
def test_application_detail_requires_login(client) -> None:
    """Anonymous users should be redirected before viewing applications."""
    owner = UserFactory()
    application = JobApplication.objects.create(
        owner=owner,
        title="Product Analyst",
        company="Example Co",
    )

    response = client.get(application.get_absolute_url())

    assert response.status_code == 302
    assert reverse("users:login") in response.url


@pytest.mark.django_db
def test_application_detail_loads_for_owner(client) -> None:
    """Application owners should be able to view their detail page."""
    owner = UserFactory()
    application = JobApplication.objects.create(
        owner=owner,
        title="Product Analyst",
        company="Example Co",
    )
    client.force_login(owner)

    response = client.get(application.get_absolute_url())

    assert response.status_code == 200
    assert response.context["application"] == application
    assert b"Product Analyst" in response.content


@pytest.mark.django_db
def test_application_detail_hides_other_users_applications(client) -> None:
    """Users should not be able to view applications they do not own."""
    owner = UserFactory(email="owner@example.com")
    other_user = UserFactory(email="other@example.com")
    application = JobApplication.objects.create(
        owner=owner,
        title="Product Analyst",
        company="Example Co",
    )
    client.force_login(other_user)

    response = client.get(application.get_absolute_url())

    assert response.status_code == 404


@pytest.mark.django_db
def test_application_list_loads_empty_preview_for_anonymous_user(client) -> None:
    """Anonymous users should see an empty application-list preview."""
    response = client.get(reverse("jobs:application_list"))

    assert response.status_code == 200
    assert b"No job applications yet" in response.content


@pytest.mark.django_db
def test_application_list_shows_only_owned_applications(client) -> None:
    """The application list should be scoped to the current user."""
    owner = UserFactory(email="owner@example.com")
    other_user = UserFactory(email="other@example.com")
    owned_application = JobApplication.objects.create(
        owner=owner,
        title="Product Analyst",
        company="Example Co",
    )
    JobApplication.objects.create(
        owner=other_user,
        title="Hidden Analyst",
        company="Other Co",
    )
    client.force_login(owner)

    response = client.get(reverse("jobs:application_list"))

    assert response.status_code == 200
    assert list(response.context["applications"]) == [owned_application]
    assert b"Product Analyst" in response.content
    assert b"Example Co" in response.content
    assert b"Saved" in response.content
    assert b"Not recorded" in response.content
    assert b"View" in response.content
    assert b"Hidden Analyst" not in response.content


@pytest.mark.django_db
def test_application_list_renders_empty_state(client) -> None:
    """The application list should show an empty state without applications."""
    owner = UserFactory()
    client.force_login(owner)

    response = client.get(reverse("jobs:application_list"))

    assert response.status_code == 200
    assert b"No job applications yet" in response.content
    assert b"Add your first application" in response.content


@pytest.mark.django_db
def test_application_detail_adds_note_for_owner(client) -> None:
    """Application owners should be able to add inline notes."""
    owner = UserFactory()
    application = JobApplication.objects.create(
        owner=owner,
        title="Product Analyst",
        company="Example Co",
    )
    client.force_login(owner)

    response = client.post(
        application.get_absolute_url(),
        {
            "body": "Follow up with recruiter.",
        },
    )

    note = ApplicationNote.objects.get(application=application)
    assert response.status_code == 302
    assert response["Location"] == application.get_absolute_url()
    assert note.body == "Follow up with recruiter."


@pytest.mark.django_db
def test_application_detail_redisplays_invalid_note_form(client) -> None:
    """Invalid note submissions should keep the user on the detail page."""
    owner = UserFactory()
    application = JobApplication.objects.create(
        owner=owner,
        title="Product Analyst",
        company="Example Co",
    )
    client.force_login(owner)

    response = client.post(
        application.get_absolute_url(),
        {
            "body": " ",
        },
    )

    assert response.status_code == 200
    assert b"Please correct the note errors below." in response.content
    assert ApplicationNote.objects.filter(application=application).count() == 0


@pytest.mark.django_db
def test_application_create_renders_empty_form_for_authenticated_user() -> None:
    """The create view should render the job application form."""
    user = UserFactory()
    request = RequestFactory().get("/applications/new/")
    request.user = user

    response = application_create(request)

    assert response.status_code == 200
    assert b"Add job application" in response.content
    assert b"Create application" in response.content
    assert b'value="saved" selected' in response.content


@pytest.mark.django_db
def test_application_create_saves_application_for_current_user() -> None:
    """Valid create submissions should create an application owned by the user."""
    user = UserFactory()
    request = RequestFactory().post(
        "/applications/new/",
        {
            "title": "Backend Engineer",
            "company": "Example Co",
            "status": JobApplication.Status.APPLIED,
            "job_link": "https://example.com/jobs/backend-engineer",
            "applied_date": "2026-05-01",
            "job_description": "Build Django product workflows.",
            "notes": "Applied through the company website.",
        },
    )
    request.user = user
    add_request_messages(request)

    response = application_create(request)
    application = JobApplication.objects.get(owner=user)

    assert response.status_code == 302
    assert response["Location"] == application.get_absolute_url()
    assert application.title == "Backend Engineer"
    assert application.company == "Example Co"
    assert application.status == JobApplication.Status.APPLIED


@pytest.mark.django_db
def test_application_create_redisplays_invalid_form() -> None:
    """Invalid create submissions should redisplay the form with errors."""
    user = UserFactory()
    request = RequestFactory().post(
        "/applications/new/",
        {
            "title": " ",
            "company": "",
            "status": JobApplication.Status.SAVED,
        },
    )
    request.user = user
    add_request_messages(request)

    response = application_create(request)

    assert response.status_code == 200
    assert b"Please correct the errors below." in response.content
    assert JobApplication.objects.filter(owner=user).count() == 0


@pytest.mark.django_db
def test_application_update_loads_for_owner(client) -> None:
    """Application owners should be able to load the edit form."""
    owner = UserFactory()
    application = JobApplication.objects.create(
        owner=owner,
        title="Product Analyst",
        company="Example Co",
    )
    client.force_login(owner)

    response = client.get(
        reverse("jobs:application_update", kwargs={"pk": application.pk})
    )

    assert response.status_code == 200
    assert response.context["application"] == application
    assert b"Edit job application" in response.content


@pytest.mark.django_db
def test_application_update_saves_changes_for_owner(client) -> None:
    """Valid update submissions should persist changes."""
    owner = UserFactory()
    application = JobApplication.objects.create(
        owner=owner,
        title="Product Analyst",
        company="Example Co",
    )
    client.force_login(owner)

    response = client.post(
        reverse("jobs:application_update", kwargs={"pk": application.pk}),
        {
            "title": "Senior Product Analyst",
            "company": "Example Co",
            "status": JobApplication.Status.INTERVIEWING,
            "job_link": "",
            "applied_date": "",
            "job_description": "Analyse product data.",
            "notes": "Panel interview booked.",
        },
    )

    application.refresh_from_db()
    assert response.status_code == 302
    assert response["Location"] == application.get_absolute_url()
    assert application.title == "Senior Product Analyst"
    assert application.status == JobApplication.Status.INTERVIEWING


@pytest.mark.django_db
def test_application_update_redisplays_invalid_form(client) -> None:
    """Invalid update submissions should redisplay errors."""
    owner = UserFactory()
    application = JobApplication.objects.create(
        owner=owner,
        title="Product Analyst",
        company="Example Co",
    )
    client.force_login(owner)

    response = client.post(
        reverse("jobs:application_update", kwargs={"pk": application.pk}),
        {
            "title": "",
            "company": "",
            "status": JobApplication.Status.SAVED,
        },
    )

    application.refresh_from_db()
    assert response.status_code == 200
    assert b"Please correct the errors below." in response.content
    assert application.title == "Product Analyst"


@pytest.mark.django_db
def test_application_delete_loads_confirmation_for_owner(client) -> None:
    """Application owners should be able to load the delete confirmation."""
    owner = UserFactory()
    application = JobApplication.objects.create(
        owner=owner,
        title="Product Analyst",
        company="Example Co",
    )
    client.force_login(owner)

    response = client.get(
        reverse("jobs:application_delete", kwargs={"pk": application.pk})
    )

    assert response.status_code == 200
    assert b"Delete Product Analyst?" in response.content


@pytest.mark.django_db
def test_application_delete_removes_owned_application(client) -> None:
    """POSTing the confirmation should delete the owned application."""
    owner = UserFactory()
    application = JobApplication.objects.create(
        owner=owner,
        title="Product Analyst",
        company="Example Co",
    )
    client.force_login(owner)

    response = client.post(
        reverse("jobs:application_delete", kwargs={"pk": application.pk})
    )

    assert response.status_code == 302
    assert response["Location"] == reverse("jobs:application_list")
    assert JobApplication.objects.filter(pk=application.pk).count() == 0
