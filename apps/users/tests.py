"""Tests for Trackly user identity behavior."""

import pytest
from django.contrib.auth import get_user_model

pytestmark = pytest.mark.django_db


def test_create_user_uses_email_as_login_identifier() -> None:
    """User creation normalizes email and stores a usable password."""
    user_model = get_user_model()

    user = user_model.objects.create_user(
        email="Person@EXAMPLE.COM",
        password="password123",
    )

    assert user.username is None
    assert user.email == "Person@example.com"
    assert user.check_password("password123")


def test_create_user_requires_email() -> None:
    """Users cannot be created without an email address."""
    user_model = get_user_model()

    with pytest.raises(ValueError, match="Users must provide an email address."):
        user_model.objects.create_user(email="")


def test_create_superuser_sets_required_admin_flags() -> None:
    """Superuser creation sets Django admin permission flags."""
    user_model = get_user_model()

    user = user_model.objects.create_superuser(
        email="admin@example.com",
        password="password123",
    )

    assert user.is_staff is True
    assert user.is_superuser is True
    assert user.is_active is True


@pytest.mark.parametrize(
    ("extra_fields", "message"),
    [
        ({"is_staff": False}, "Superusers must have is_staff=True."),
        ({"is_superuser": False}, "Superusers must have is_superuser=True."),
    ],
)
def test_create_superuser_rejects_missing_permission_flags(
    extra_fields: dict[str, bool],
    message: str,
) -> None:
    """Superusers must keep the required Django permission flags."""
    user_model = get_user_model()

    with pytest.raises(ValueError, match=message):
        user_model.objects.create_superuser(
            email="admin@example.com",
            password="password123",
            **extra_fields,
        )


def test_user_string_uses_email() -> None:
    """The user string representation is stable and email-based."""
    user_model = get_user_model()
    user = user_model.objects.create_user(email="person@example.com")

    assert str(user) == "person@example.com"


def test_display_name_prefers_full_name() -> None:
    """Display names use full names when profile names are available."""
    user_model = get_user_model()
    user = user_model.objects.create_user(
        email="person@example.com",
        first_name="Ada",
        last_name="Lovelace",
    )

    assert user.display_name == "Ada Lovelace"


def test_display_name_falls_back_to_email() -> None:
    """Display names fall back to email for incomplete profiles."""
    user_model = get_user_model()
    user = user_model.objects.create_user(email="person@example.com")

    assert user.display_name == "person@example.com"
