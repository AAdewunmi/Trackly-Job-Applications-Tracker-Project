"""Model tests for the custom Trackly user model."""

import pytest

from apps.roles.factories import RoleFactory
from apps.users.factories import UserFactory
from apps.users.models import User


@pytest.mark.django_db
def test_user_creation_uses_email_as_identifier() -> None:
    """Users should authenticate with email rather than username."""
    user = User.objects.create_user(
        email="Ada@Example.COM",
        password="StrongPass12345!",
    )

    assert user.email == "Ada@example.com"
    assert user.username is None
    assert user.check_password("StrongPass12345!") is True


@pytest.mark.django_db
def test_create_user_requires_email() -> None:
    """Creating a user without an email should fail clearly."""
    with pytest.raises(ValueError, match="email address"):
        User.objects.create_user(email="", password="StrongPass12345!")


@pytest.mark.django_db
def test_superuser_has_expected_flags() -> None:
    """Superusers should always be staff, superuser, and active."""
    user = User.objects.create_superuser(
        email="admin@example.com",
        password="StrongPass12345!",
    )

    assert user.is_staff is True
    assert user.is_superuser is True
    assert user.is_active is True


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("extra_fields", "message"),
    [
        ({"is_staff": False}, "Superusers must have is_staff=True."),
        ({"is_superuser": False}, "Superusers must have is_superuser=True."),
    ],
)
def test_superuser_rejects_missing_permission_flags(
    extra_fields: dict[str, bool],
    message: str,
) -> None:
    """Superusers must keep the required Django permission flags."""
    with pytest.raises(ValueError, match=message):
        User.objects.create_superuser(
            email="admin@example.com",
            password="StrongPass12345!",
            **extra_fields,
        )


@pytest.mark.django_db
def test_user_string_uses_email() -> None:
    """User string conversion should expose the stable email label."""
    user = UserFactory(email="person@example.com")

    assert str(user) == "person@example.com"


@pytest.mark.django_db
def test_display_name_prefers_full_name() -> None:
    """Display name should use the full name when one exists."""
    user = UserFactory(first_name="Grace", last_name="Hopper")

    assert user.display_name == "Grace Hopper"


@pytest.mark.django_db
def test_display_name_falls_back_to_email() -> None:
    """Display name should fall back to email when no full name exists."""
    user = UserFactory(
        email="person@example.com",
        first_name="",
        last_name="",
    )

    assert user.display_name == "person@example.com"


@pytest.mark.django_db
def test_user_can_be_assigned_product_role() -> None:
    """Users should support product role assignment through the roles relation."""
    role = RoleFactory()
    user = UserFactory()

    user.roles.add(role)

    assert user.roles.filter(code=role.code).exists() is True
