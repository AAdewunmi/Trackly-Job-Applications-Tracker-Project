"""Views for Trackly dashboards."""

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from apps.dashboard.services import get_user_dashboard_context
from apps.roles.models import Role
from apps.roles.permissions import can_access_user_workspace, is_trackly_admin


@login_required
def user_index(request: HttpRequest) -> HttpResponse:
    """Render the authenticated user's dashboard."""
    if not can_access_user_workspace(request.user):
        raise PermissionDenied("Admin users cannot access the user dashboard.")

    dashboard_context = get_user_dashboard_context(request.user)

    return render(
        request,
        "dashboard/user_index.html",
        {
            "page_title": "Dashboard",
            "metrics": dashboard_context.metrics,
            "recent_applications": dashboard_context.recent_applications,
            "saved_applications": dashboard_context.saved_applications,
            "applied_applications": dashboard_context.applied_applications,
            "interviewing_applications": dashboard_context.interviewing_applications,
            "recent_insights": dashboard_context.recent_insights,
            "target_profiles": dashboard_context.target_profiles,
        },
    )


@login_required
def admin_index(request: HttpRequest) -> HttpResponse:
    """Render the protected admin dashboard shell."""
    if not is_trackly_admin(request.user):
        raise PermissionDenied("You do not have permission to access this dashboard.")

    user_model = get_user_model()

    return render(
        request,
        "dashboard/admin_index.html",
        {
            "page_title": "Admin Dashboard",
            "total_users": user_model.objects.count(),
            "total_roles": Role.objects.count(),
        },
    )
