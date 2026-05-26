"""Factory tests for Trackly users."""

import pytest

from apps.roles.factories import AdminRoleFactory, RoleFactory
from apps.users.factories import MemberUserFactory, StaffUserFactory, UserFactory


@pytest.mark.django_db
def test_user_factory_sets_default_password() -> None:
    """UserFactory creates persisted users with a usable default password."""
    user = UserFactory()

    assert user.check_password("StrongPass12345!") is True


@pytest.mark.django_db
def test_user_factory_accepts_custom_password() -> None:
    """UserFactory accepts an explicit raw password."""
    user = UserFactory(password="DifferentPass12345!")

    assert user.check_password("DifferentPass12345!") is True


@pytest.mark.django_db
def test_user_factory_attaches_supplied_roles() -> None:
    """UserFactory attaches explicitly supplied roles."""
    role = AdminRoleFactory()
    user = UserFactory(roles=[role])

    assert user.roles.filter(code=role.code).exists() is True


def test_user_factory_build_skips_role_attachment() -> None:
    """Build-only users skip many-to-many role writes."""
    role = RoleFactory.build()
    user = UserFactory.build(roles=[role])

    assert user.pk is None


@pytest.mark.django_db
def test_member_user_factory_creates_member_role() -> None:
    """MemberUserFactory attaches the default member role."""
    user = MemberUserFactory()

    assert user.roles.filter(code=RoleFactory.code).exists() is True


@pytest.mark.django_db
def test_member_user_factory_accepts_supplied_roles() -> None:
    """MemberUserFactory uses supplied roles instead of the default member role."""
    role = AdminRoleFactory()
    user = MemberUserFactory(roles=[role])

    assert user.roles.filter(code=role.code).exists() is True
    assert user.roles.filter(code=RoleFactory.code).exists() is False


def test_member_user_factory_build_skips_default_role() -> None:
    """Build-only member users skip default role creation."""
    user = MemberUserFactory.build()

    assert user.pk is None


@pytest.mark.django_db
def test_staff_user_factory_creates_staff_user() -> None:
    """StaffUserFactory creates staff users for admin-surface tests."""
    user = StaffUserFactory()

    assert user.is_staff is True
