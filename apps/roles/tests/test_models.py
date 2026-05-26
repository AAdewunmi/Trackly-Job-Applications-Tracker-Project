"""Model tests for Trackly roles."""

import pytest
from django.db import IntegrityError

from apps.roles.factories import RoleFactory
from apps.roles.models import Role


@pytest.mark.django_db
def test_role_string_returns_name() -> None:
    """Role string conversion should expose the readable role name."""
    role = RoleFactory(name="Career Coach")

    assert str(role) == "Career Coach"


@pytest.mark.django_db
def test_role_code_must_be_unique() -> None:
    """Role codes should be unique so permissions remain unambiguous."""
    Role.objects.create(code=Role.Codes.MEMBER, name="Member")

    with pytest.raises(IntegrityError):
        Role.objects.create(code=Role.Codes.MEMBER, name="Duplicate Member")


@pytest.mark.django_db
def test_inactive_role_can_be_stored() -> None:
    """Inactive roles should persist for safe future deactivation workflows."""
    role = RoleFactory(is_active=False)

    assert role.is_active is False
