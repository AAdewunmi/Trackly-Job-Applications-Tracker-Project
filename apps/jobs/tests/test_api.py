"""API tests for job application endpoints."""

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.jobs.factories import ApplicationNoteFactory, JobApplicationFactory
from apps.jobs.models import ApplicationNote, JobApplication
from apps.users.factories import UserFactory


def valid_application_payload(**overrides: object) -> dict[str, object]:
    """Return a valid API payload for a job application."""
    payload = {
        "title": "Backend Engineer",
        "company": "Example Ltd",
        "status": JobApplication.Status.APPLIED,
        "job_link": "https://example.com/jobs/backend-engineer",
        "applied_date": timezone.localdate().isoformat(),
        "job_description": "Build Django services and maintain APIs.",
        "notes": "Applied through the company careers page.",
    }
    payload.update(overrides)
    return payload


@pytest.fixture
def api_client() -> APIClient:
    """Return a DRF API client."""
    return APIClient()


@pytest.mark.django_db
def test_application_api_rejects_unauthenticated_requests(api_client) -> None:
    """Anonymous API requests should be rejected by default permissions."""
    response = api_client.get(reverse("job-application-list-create"))

    assert response.status_code == 401


@pytest.mark.django_db
def test_application_api_lists_only_authenticated_users_records(api_client) -> None:
    """The list endpoint should not expose another user's applications."""
    user = UserFactory()
    other_user = UserFactory()
    own_application = JobApplicationFactory(owner=user, title="Own Role")
    JobApplicationFactory(owner=other_user, title="Other Role")
    api_client.force_authenticate(user=user)

    response = api_client.get(reverse("job-application-list-create"))

    assert response.status_code == 200
    titles = [application["title"] for application in response.data]
    assert titles == [own_application.title]


@pytest.mark.django_db
def test_application_api_detail_includes_application_notes(api_client) -> None:
    """Application detail should expose notes from the browser workflow."""
    user = UserFactory()
    application = JobApplicationFactory(owner=user)
    note = ApplicationNoteFactory(
        application=application,
        body="Interview scheduled for Thursday.",
    )
    api_client.force_authenticate(user=user)

    response = api_client.get(
        reverse("job-application-detail", kwargs={"pk": application.pk})
    )

    assert response.status_code == 200
    assert response.data["application_notes"] == [
        {
            "id": note.id,
            "body": "Interview scheduled for Thursday.",
            "created_at": response.data["application_notes"][0]["created_at"],
            "updated_at": response.data["application_notes"][0]["updated_at"],
        }
    ]


@pytest.mark.django_db
def test_application_api_create_assigns_owner_from_request_user(api_client) -> None:
    """The create endpoint should ignore posted ownership and use request.user."""
    user = UserFactory()
    other_user = UserFactory()
    api_client.force_authenticate(user=user)

    response = api_client.post(
        reverse("job-application-list-create"),
        data={**valid_application_payload(), "owner": other_user.pk},
        format="json",
    )

    assert response.status_code == 201
    application = JobApplication.objects.get()
    assert application.owner == user
    assert application.title == "Backend Engineer"


@pytest.mark.django_db
def test_application_api_retrieves_owned_application(api_client) -> None:
    """The detail endpoint should retrieve the authenticated user's application."""
    user = UserFactory()
    application = JobApplicationFactory(owner=user, title="Product Analyst")
    api_client.force_authenticate(user=user)

    response = api_client.get(f"/api/v1/jobs/applications/{application.pk}/")

    assert response.status_code == 200
    assert response.data["id"] == application.id
    assert response.data["title"] == "Product Analyst"


@pytest.mark.django_db
def test_application_api_updates_owned_application(api_client) -> None:
    """The detail endpoint should update the authenticated user's application."""
    user = UserFactory()
    application = JobApplicationFactory(owner=user, title="Original Role")
    api_client.force_authenticate(user=user)

    response = api_client.patch(
        f"/api/v1/jobs/applications/{application.pk}/",
        data={"title": "Updated Role"},
        format="json",
    )

    application.refresh_from_db()
    assert response.status_code == 200
    assert application.title == "Updated Role"


@pytest.mark.django_db
def test_application_api_deletes_owned_application(api_client) -> None:
    """The detail endpoint should delete the authenticated user's application."""
    user = UserFactory()
    application = JobApplicationFactory(owner=user)
    api_client.force_authenticate(user=user)

    response = api_client.delete(f"/api/v1/jobs/applications/{application.pk}/")

    assert response.status_code == 204
    assert not JobApplication.objects.filter(pk=application.pk).exists()


@pytest.mark.django_db
def test_application_api_detail_hides_other_users_records(api_client) -> None:
    """Users should receive 404 for another user's application detail."""
    user = UserFactory()
    other_application = JobApplicationFactory(owner=UserFactory())
    api_client.force_authenticate(user=user)

    response = api_client.get(
        reverse("job-application-detail", kwargs={"pk": other_application.pk})
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_application_api_update_hides_other_users_records(api_client) -> None:
    """Users should not be able to update another user's application."""
    user = UserFactory()
    other_application = JobApplicationFactory(
        owner=UserFactory(),
        title="Original Role",
    )
    api_client.force_authenticate(user=user)

    response = api_client.patch(
        reverse("job-application-detail", kwargs={"pk": other_application.pk}),
        data={"title": "Changed Role"},
        format="json",
    )

    other_application.refresh_from_db()
    assert response.status_code == 404
    assert other_application.title == "Original Role"


@pytest.mark.django_db
def test_application_api_delete_hides_other_users_records(api_client) -> None:
    """Users should not be able to delete another user's application."""
    user = UserFactory()
    other_application = JobApplicationFactory(owner=UserFactory())
    api_client.force_authenticate(user=user)

    response = api_client.delete(
        reverse("job-application-detail", kwargs={"pk": other_application.pk})
    )

    assert response.status_code == 404
    assert JobApplication.objects.filter(pk=other_application.pk).exists()


@pytest.mark.django_db
def test_application_note_api_rejects_unauthenticated_requests(api_client) -> None:
    """Anonymous API requests should not access application notes."""
    application = JobApplicationFactory()

    response = api_client.get(
        reverse(
            "application-note-list-create",
            kwargs={"application_pk": application.pk},
        )
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_application_note_api_lists_only_parent_application_notes(api_client) -> None:
    """The notes endpoint should list notes for the owned parent application."""
    user = UserFactory()
    application = JobApplicationFactory(owner=user)
    other_application = JobApplicationFactory(owner=user)
    note = ApplicationNoteFactory(application=application, body="Send portfolio.")
    ApplicationNoteFactory(application=other_application, body="Different note.")
    api_client.force_authenticate(user=user)

    response = api_client.get(
        reverse(
            "application-note-list-create",
            kwargs={"application_pk": application.pk},
        )
    )

    assert response.status_code == 200
    assert [item["body"] for item in response.data] == [note.body]


@pytest.mark.django_db
def test_application_note_api_creates_note_for_owned_application(api_client) -> None:
    """The note create endpoint should attach notes to the owned application."""
    user = UserFactory()
    application = JobApplicationFactory(owner=user)
    api_client.force_authenticate(user=user)

    response = api_client.post(
        reverse(
            "application-note-list-create",
            kwargs={"application_pk": application.pk},
        ),
        data={"body": "  Recruiter asked for availability.  "},
        format="json",
    )

    assert response.status_code == 201
    note = ApplicationNote.objects.get(application=application)
    assert note.body == "Recruiter asked for availability."


@pytest.mark.django_db
def test_application_note_api_retrieves_owned_note(api_client) -> None:
    """The note detail endpoint should retrieve notes on owned applications."""
    user = UserFactory()
    application = JobApplicationFactory(owner=user)
    note = ApplicationNoteFactory(application=application, body="Follow up tomorrow.")
    api_client.force_authenticate(user=user)

    response = api_client.get(
        reverse(
            "application-note-detail",
            kwargs={"application_pk": application.pk, "pk": note.pk},
        )
    )

    assert response.status_code == 200
    assert response.data["id"] == note.id
    assert response.data["body"] == "Follow up tomorrow."


@pytest.mark.django_db
def test_application_note_api_updates_owned_note(api_client) -> None:
    """The note detail endpoint should update notes on owned applications."""
    user = UserFactory()
    application = JobApplicationFactory(owner=user)
    note = ApplicationNoteFactory(application=application, body="Original note.")
    api_client.force_authenticate(user=user)

    response = api_client.patch(
        reverse(
            "application-note-detail",
            kwargs={"application_pk": application.pk, "pk": note.pk},
        ),
        data={"body": "  Updated note.  "},
        format="json",
    )

    note.refresh_from_db()
    assert response.status_code == 200
    assert note.body == "Updated note."


@pytest.mark.django_db
def test_application_note_api_deletes_owned_note(api_client) -> None:
    """The note detail endpoint should delete notes on owned applications."""
    user = UserFactory()
    application = JobApplicationFactory(owner=user)
    note = ApplicationNoteFactory(application=application)
    api_client.force_authenticate(user=user)

    response = api_client.delete(
        reverse(
            "application-note-detail",
            kwargs={"application_pk": application.pk, "pk": note.pk},
        )
    )

    assert response.status_code == 204
    assert not ApplicationNote.objects.filter(pk=note.pk).exists()


@pytest.mark.django_db
def test_application_note_api_rejects_blank_body(api_client) -> None:
    """Blank notes should not be persisted through the API."""
    user = UserFactory()
    application = JobApplicationFactory(owner=user)
    api_client.force_authenticate(user=user)

    response = api_client.post(
        reverse(
            "application-note-list-create",
            kwargs={"application_pk": application.pk},
        ),
        data={"body": "   "},
        format="json",
    )

    assert response.status_code == 400
    assert ApplicationNote.objects.filter(application=application).count() == 0


@pytest.mark.django_db
def test_application_note_api_rejects_blank_body_update(api_client) -> None:
    """Blank note updates should not be persisted through the API."""
    user = UserFactory()
    application = JobApplicationFactory(owner=user)
    note = ApplicationNoteFactory(application=application, body="Original note.")
    api_client.force_authenticate(user=user)

    response = api_client.patch(
        reverse(
            "application-note-detail",
            kwargs={"application_pk": application.pk, "pk": note.pk},
        ),
        data={"body": "   "},
        format="json",
    )

    note.refresh_from_db()
    assert response.status_code == 400
    assert note.body == "Original note."


@pytest.mark.django_db
def test_application_note_api_hides_other_users_applications(api_client) -> None:
    """Users should not be able to list or create notes on foreign applications."""
    user = UserFactory()
    other_application = JobApplicationFactory(owner=UserFactory())
    api_client.force_authenticate(user=user)

    list_response = api_client.get(
        reverse(
            "application-note-list-create",
            kwargs={"application_pk": other_application.pk},
        )
    )
    create_response = api_client.post(
        reverse(
            "application-note-list-create",
            kwargs={"application_pk": other_application.pk},
        ),
        data={"body": "Attempted foreign note."},
        format="json",
    )

    assert list_response.status_code == 404
    assert create_response.status_code == 404
    assert ApplicationNote.objects.count() == 0


@pytest.mark.django_db
def test_application_note_api_hides_other_users_note_detail(api_client) -> None:
    """Users should not retrieve, update, or delete foreign notes."""
    user = UserFactory()
    other_application = JobApplicationFactory(owner=UserFactory())
    note = ApplicationNoteFactory(application=other_application, body="Foreign note.")
    api_client.force_authenticate(user=user)
    url = reverse(
        "application-note-detail",
        kwargs={"application_pk": other_application.pk, "pk": note.pk},
    )

    get_response = api_client.get(url)
    update_response = api_client.patch(
        url,
        data={"body": "Attempted update."},
        format="json",
    )
    delete_response = api_client.delete(url)

    note.refresh_from_db()
    assert get_response.status_code == 404
    assert update_response.status_code == 404
    assert delete_response.status_code == 404
    assert note.body == "Foreign note."


@pytest.mark.django_db
def test_application_note_api_hides_note_under_wrong_parent(api_client) -> None:
    """Owned notes should not be exposed under a different parent application."""
    user = UserFactory()
    application = JobApplicationFactory(owner=user)
    other_application = JobApplicationFactory(owner=user)
    note = ApplicationNoteFactory(application=application)
    api_client.force_authenticate(user=user)

    response = api_client.get(
        reverse(
            "application-note-detail",
            kwargs={"application_pk": other_application.pk, "pk": note.pk},
        )
    )

    assert response.status_code == 404
