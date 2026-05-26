"""Factory helpers for role tests."""

import factory

from apps.roles.models import Role


class RoleFactory(factory.django.DjangoModelFactory):
    """Create a Trackly product role for tests."""

    class Meta:
        """Factory metadata for RoleFactory."""

        model = Role
        django_get_or_create = ("code",)

    code = Role.Codes.MEMBER
    name = "Member"
    description = "Default member access."
    is_active = True
