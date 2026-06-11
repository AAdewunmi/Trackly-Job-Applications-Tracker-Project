"""Template context helpers for Trackly role-aware navigation."""

from apps.roles.permissions import is_trackly_admin


def trackly_roles(request):
    """Expose role flags used by shared templates."""
    return {
        "is_trackly_admin_user": is_trackly_admin(request.user),
    }
