"""Role permission helpers for Trackly product surfaces."""

from django.contrib.auth.models import AnonymousUser

from apps.users.models import User

from .models import Role


def is_trackly_admin(user: User | AnonymousUser) -> bool:
    """Return whether the user may access Trackly admin surfaces."""
    if not user.is_authenticated:
        return False

    if user.is_staff:
        return True

    return user.roles.filter(code=Role.Codes.ADMIN, is_active=True).exists()
