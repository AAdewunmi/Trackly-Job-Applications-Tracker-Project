"""Form tests for Trackly account workflows."""

import pytest

from apps.users.factories import UserFactory
from apps.users.forms import SignUpForm


@pytest.mark.django_db
def test_signup_form_rejects_duplicate_email() -> None:
    """Signup should reject an email already registered to a user."""
    UserFactory(email="person@example.com")

    form = SignUpForm(
        data={
            "email": "PERSON@example.com",
            "first_name": "New",
            "last_name": "User",
            "password1": "StrongPass12345!",
            "password2": "StrongPass12345!",
        }
    )

    assert form.is_valid() is False
    assert form.errors["email"] == ["A user with this email already exists."]
