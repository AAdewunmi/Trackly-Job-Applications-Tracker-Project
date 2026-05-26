"""Tests for Trackly role access-control foundations."""

import importlib

import pytest
from django.apps import apps as django_apps

from apps.roles.models import Role

pytestmark = pytest.mark.django_db


def test_role_codes_define_sprint_1_access_roles() -> None:
    """Sprint 1 roles expose stable access-control codes."""
    assert Role.Codes.ADMIN == "admin"
    assert Role.Codes.MEMBER == "member"
    assert Role.Codes.choices == [("admin", "Admin"), ("member", "Member")]


def test_role_string_uses_human_readable_name() -> None:
    """Role labels use the human-readable name."""
    role = Role.objects.create(code=Role.Codes.ADMIN, name="Admin")

    assert str(role) == "Admin"


def test_roles_order_by_code() -> None:
    """Roles are ordered by stable code instead of display name."""
    Role.objects.create(code=Role.Codes.MEMBER, name="Member")
    Role.objects.create(code=Role.Codes.ADMIN, name="Admin")

    assert list(Role.objects.values_list("code", flat=True)) == ["admin", "member"]


def test_role_code_backfill_uses_existing_names() -> None:
    """The migration backfills deterministic codes from existing role names."""
    migration = importlib.import_module(
        "apps.roles.migrations.0002_role_code_alter_role_options_and_more"
    )
    role = Role.objects.create(code=Role.Codes.MEMBER, name="Power User")

    migration.populate_role_codes(django_apps, None)

    role.refresh_from_db()
    assert role.code == "power-user"


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
