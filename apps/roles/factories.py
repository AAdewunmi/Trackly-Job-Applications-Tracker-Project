"""Factory helpers for role tests."""

import factory

from apps.roles.models import Role


class RoleFactory(factory.django.DjangoModelFactory):
    """Create a standard member role for tests."""

    class Meta:
        """Factory metadata for RoleFactory."""

        model = Role
        django_get_or_create = ("code",)

    code = Role.Codes.MEMBER
    name = "Member"
    description = "Standard Trackly product user role."
    is_active = True


class AdminRoleFactory(RoleFactory):
    """Create an admin role for tests."""

    code = Role.Codes.ADMIN
    name = "Admin"
    description = "Trackly product administrator role."
