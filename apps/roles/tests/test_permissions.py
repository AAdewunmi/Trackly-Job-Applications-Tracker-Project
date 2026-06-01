"""Tests for role-aware permission helpers."""

from types import SimpleNamespace

import pytest
from django.contrib.auth.models import AnonymousUser

from apps.roles.models import Role
from apps.roles.permissions import is_trackly_admin, user_has_role
from apps.users.factories import StaffUserFactory, UserFactory

pytestmark = pytest.mark.django_db


def test_user_has_role_returns_false_for_anonymous_user() -> None:
    """Anonymous users do not have product roles."""
    assert user_has_role(AnonymousUser(), Role.Codes.ADMIN) is False


def test_user_has_role_returns_false_for_object_without_roles() -> None:
    """Non-Trackly user-like objects should be handled safely."""
    user = object()

    assert user_has_role(user, Role.Codes.ADMIN) is False


def test_user_has_role_returns_false_for_authenticated_object_without_roles() -> None:
    """Authenticated non-Trackly user-like objects should be handled safely."""
    user = SimpleNamespace(is_authenticated=True)

    assert user_has_role(user, Role.Codes.ADMIN) is False


def test_user_has_role_requires_active_matching_role() -> None:
    """Only active roles with the requested code should match."""
    role = Role.objects.create(code=Role.Codes.MEMBER, name="Member")
    inactive_admin_role = Role.objects.create(
        code=Role.Codes.ADMIN,
        name="Admin",
        is_active=False,
    )
    user = UserFactory()
    user.roles.add(role, inactive_admin_role)

    assert user_has_role(user, Role.Codes.MEMBER) is True
    assert user_has_role(user, Role.Codes.ADMIN) is False


def test_is_trackly_admin_allows_staff_user() -> None:
    """Django staff users can access Trackly admin surfaces."""
    user = StaffUserFactory()

    assert is_trackly_admin(user) is True


def test_is_trackly_admin_returns_false_for_anonymous_user() -> None:
    """Anonymous users should not access Trackly admin surfaces."""
    assert is_trackly_admin(AnonymousUser()) is False


def test_is_trackly_admin_returns_false_for_unauthenticated_object() -> None:
    """Unauthenticated user-like objects should not receive admin access."""
    user = SimpleNamespace(is_authenticated=False)

    assert is_trackly_admin(user) is False


def test_is_trackly_admin_allows_active_admin_role() -> None:
    """Users with an active admin role can access Trackly admin surfaces."""
    role = Role.objects.create(code=Role.Codes.ADMIN, name="Admin")
    user = UserFactory()
    user.roles.add(role)

    assert is_trackly_admin(user) is True


def test_is_trackly_admin_denies_standard_user() -> None:
    """Standard users without admin access are denied."""
    user = UserFactory()

    assert is_trackly_admin(user) is False
