"""Integration tests for Trackly authentication views."""

import pytest
from django.urls import reverse

from apps.users.factories import UserFactory
from apps.users.models import User


@pytest.mark.django_db
def test_signup_page_loads(client) -> None:
    """The signup page should be reachable by anonymous visitors."""
    response = client.get(reverse("users:signup"))

    assert response.status_code == 200
    assert b"Create your Trackly account" in response.content


@pytest.mark.django_db
def test_signup_creates_user_and_logs_them_in(client) -> None:
    """A valid signup should create the user and start an authenticated session."""
    response = client.post(
        reverse("users:signup"),
        data={
            "email": "new.user@example.com",
            "first_name": "New",
            "last_name": "User",
            "password1": "StrongPass12345!",
            "password2": "StrongPass12345!",
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("dashboard:user")
    assert User.objects.filter(email="new.user@example.com").exists() is True
    assert "_auth_user_id" in client.session


@pytest.mark.django_db
def test_signup_rejects_duplicate_email(client) -> None:
    """The signup form should reject a duplicate email address."""
    UserFactory(email="taken@example.com")

    response = client.post(
        reverse("users:signup"),
        data={
            "email": "taken@example.com",
            "first_name": "Taken",
            "last_name": "User",
            "password1": "StrongPass12345!",
            "password2": "StrongPass12345!",
        },
    )

    assert response.status_code == 200
    assert b"A user with this email already exists." in response.content


@pytest.mark.django_db
def test_login_with_email_succeeds(client) -> None:
    """Users should be able to sign in with email and password."""
    UserFactory(email="login@example.com", password="StrongPass12345!")

    response = client.post(
        reverse("users:login"),
        data={
            "username": "login@example.com",
            "password": "StrongPass12345!",
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("dashboard:user")
    assert "_auth_user_id" in client.session


@pytest.mark.django_db
def test_profile_requires_authentication(client) -> None:
    """Anonymous users should be redirected away from the profile page."""
    response = client.get(reverse("users:profile"))

    assert response.status_code == 302
    assert reverse("users:login") in response.url


@pytest.mark.django_db
def test_profile_displays_authenticated_user(client) -> None:
    """Authenticated users should see their profile details."""
    user = UserFactory(
        email="profile@example.com",
        first_name="Profile",
        last_name="Owner",
    )
    client.force_login(user)

    response = client.get(reverse("users:profile"))

    assert response.status_code == 200
    assert b"profile@example.com" in response.content
    assert b"Profile Owner" in response.content


@pytest.mark.django_db
def test_logout_redirects_to_login(client) -> None:
    """Logout should clear the session and return the user to login."""
    user = UserFactory()
    client.force_login(user)

    response = client.post(reverse("users:logout"))

    assert response.status_code == 302
    assert response.url == reverse("users:login")