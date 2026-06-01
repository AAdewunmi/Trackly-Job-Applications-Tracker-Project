"""View tests for Trackly user account workflows."""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.urls import reverse

from apps.users.factories import UserFactory


@pytest.mark.django_db
def test_signup_creates_user_and_signs_them_in(client) -> None:
    """Signup creates a user account and authenticates the session."""
    response = client.post(
        reverse("users:signup"),
        {
            "email": "new-user@example.com",
            "first_name": "New",
            "last_name": "User",
            "password1": "StrongPass12345!",
            "password2": "StrongPass12345!",
        },
    )

    user = get_user_model().objects.get(email="new-user@example.com")
    messages = [str(message) for message in get_messages(response.wsgi_request)]

    assert response.status_code == 302
    assert response["Location"] == reverse("dashboard:user")
    assert int(client.session["_auth_user_id"]) == user.pk
    assert "Your Trackly account has been created." in messages


@pytest.mark.django_db
def test_login_uses_email_authentication_form(client) -> None:
    """Login accepts the custom user email field."""
    user = UserFactory(email="person@example.com", password="StrongPass12345!")

    response = client.post(
        reverse("users:login"),
        {
            "username": user.email,
            "password": "StrongPass12345!",
        },
    )

    messages = [str(message) for message in get_messages(response.wsgi_request)]

    assert response.status_code == 302
    assert response["Location"] == reverse("dashboard:user")
    assert int(client.session["_auth_user_id"]) == user.pk
    assert "You are signed in." in messages


@pytest.mark.django_db
def test_logout_redirects_to_login_and_adds_message(client) -> None:
    """Logout clears the session and redirects to login."""
    user = UserFactory()
    client.force_login(user)

    response = client.post(reverse("users:logout"))
    messages = [str(message) for message in get_messages(response.wsgi_request)]

    assert response.status_code == 302
    assert response["Location"] == reverse("users:login")
    assert "_auth_user_id" not in client.session
    assert "You have signed out." in messages


@pytest.mark.django_db
def test_anonymous_logout_redirects_to_login_without_message(client) -> None:
    """Anonymous logout requests should redirect without a signed-out message."""
    response = client.post(reverse("users:logout"))
    messages = [str(message) for message in get_messages(response.wsgi_request)]

    assert response.status_code == 302
    assert response["Location"] == reverse("users:login")
    assert "You have signed out." not in messages


@pytest.mark.django_db
def test_profile_requires_login(client) -> None:
    """Anonymous users are redirected away from the profile page."""
    response = client.get(reverse("users:profile"))

    assert response.status_code == 302
    assert response["Location"].startswith(f"{reverse('users:login')}?next=")


@pytest.mark.django_db
def test_profile_renders_authenticated_user(client) -> None:
    """Authenticated users can view their profile page."""
    user = UserFactory(first_name="Ada", last_name="Lovelace")
    client.force_login(user)

    response = client.get(reverse("users:profile"))

    assert response.status_code == 200
    assert b"Ada Lovelace" in response.content
