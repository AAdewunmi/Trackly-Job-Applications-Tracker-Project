"""Views for Trackly dashboards."""

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from apps.dashboard.services import (
    get_admin_dashboard_context,
    get_user_dashboard_context,
)
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
            "status_chart": dashboard_context.status_chart,
            "funnel_chart": dashboard_context.funnel_chart,
        },
    )


@login_required
def admin_index(request: HttpRequest) -> HttpResponse:
    """Render the protected admin dashboard shell."""
    if not is_trackly_admin(request.user):
        raise PermissionDenied("You do not have permission to access this dashboard.")

    admin_context = get_admin_dashboard_context(
        application_search=request.GET.get("q", "").strip(),
        application_status=request.GET.get("status", "").strip(),
        application_sort=request.GET.get("sort", "-updated_at").strip(),
        application_page=request.GET.get("page", 1),
    )

    return render(
        request,
        "dashboard/admin_index.html",
        {
            "page_title": "Admin Dashboard",
            "admin_context": admin_context,
            "total_users": admin_context.total_users,
            "total_roles": admin_context.total_roles,
        },
    )
