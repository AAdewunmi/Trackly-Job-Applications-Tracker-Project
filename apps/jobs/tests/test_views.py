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
    request = RequestFactory().get("/jobs/applications/new/")
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
        "/jobs/applications/new/",
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
        "/jobs/applications/new/",
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
