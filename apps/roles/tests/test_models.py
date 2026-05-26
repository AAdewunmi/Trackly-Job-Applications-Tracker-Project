"""Model tests for Trackly roles."""

import importlib

import pytest
from django.apps import apps as django_apps
from django.db import IntegrityError

from apps.roles.factories import RoleFactory
from apps.roles.models import Role


@pytest.mark.django_db
def test_role_codes_define_sprint_1_access_roles() -> None:
    """Sprint 1 roles expose stable access-control codes."""
    assert Role.Codes.ADMIN == "admin"
    assert Role.Codes.MEMBER == "member"
    assert Role.Codes.choices == [("admin", "Admin"), ("member", "Member")]


@pytest.mark.django_db
def test_role_string_returns_name() -> None:
    """Role string conversion should expose the readable role name."""
    role = RoleFactory(name="Career Coach")

    assert str(role) == "Career Coach"


@pytest.mark.django_db
def test_roles_order_by_code() -> None:
    """Roles are ordered by stable code instead of display name."""
    Role.objects.create(code=Role.Codes.MEMBER, name="Member")
    Role.objects.create(code=Role.Codes.ADMIN, name="Admin")

    assert list(Role.objects.values_list("code", flat=True)) == ["admin", "member"]


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


@pytest.mark.django_db
def test_role_code_backfill_uses_existing_names() -> None:
    """The migration backfills deterministic codes from existing role names."""
    migration = importlib.import_module(
        "apps.roles.migrations.0002_role_code_alter_role_options_and_more"
    )
    role = Role.objects.create(code=Role.Codes.MEMBER, name="Power User")

    migration.populate_role_codes(django_apps, None)

    role.refresh_from_db()
    assert role.code == "power-user"


@pytest.mark.django_db
def test_role_code_backfill_suffixes_duplicate_names() -> None:
    """The migration keeps generated role codes unique for duplicate names."""
    migration = importlib.import_module(
        "apps.roles.migrations.0002_role_code_alter_role_options_and_more"
    )
    first_role = Role.objects.create(code="legacy-one", name="Support Lead")
    second_role = Role.objects.create(code="legacy-two", name="Support Lead")

    migration.populate_role_codes(django_apps, None)

    first_role.refresh_from_db()
    second_role.refresh_from_db()

    assert first_role.code == "support-lead"
    assert second_role.code == f"support-lead-{second_role.pk}"
