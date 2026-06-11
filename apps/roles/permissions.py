"""Permission helpers for Trackly role-aware access control."""

from django.contrib.auth.models import AnonymousUser

from apps.roles.models import Role


def user_has_role(user: object, role_code: str) -> bool:
    """Return whether a user has an active role with the given code."""
    if isinstance(user, AnonymousUser):
        return False

    is_authenticated = getattr(user, "is_authenticated", False)

    if not is_authenticated:
        return False

    # The roles relation only exists on Trackly's custom user model.
    roles = getattr(user, "roles", None)

    if roles is None:
        return False

    return roles.filter(code=role_code, is_active=True).exists()


def is_trackly_admin(user: object) -> bool:
    """Return whether a user can access Trackly admin product surfaces."""
    if isinstance(user, AnonymousUser):
        return False

    is_authenticated = getattr(user, "is_authenticated", False)

    if not is_authenticated:
        return False

    # Django staff users are allowed so the built-in admin and product admin
    # expectations do not diverge in early development.
    if getattr(user, "is_staff", False):
        return True

    return user_has_role(user, Role.Codes.ADMIN)


def can_access_user_workspace(user: object) -> bool:
    """Return whether a user can access end-user dashboard and application flows."""
    if isinstance(user, AnonymousUser):
        return False

    is_authenticated = getattr(user, "is_authenticated", False)

    if not is_authenticated:
        return False

    return not is_trackly_admin(user)
