"""Dashboard views."""

from django.http import HttpRequest, HttpResponse


def user_dashboard(request: HttpRequest) -> HttpResponse:
    """Render the user dashboard placeholder."""
    return HttpResponse("Trackly dashboard")


def admin_dashboard(request: HttpRequest) -> HttpResponse:
    """Render the admin dashboard placeholder."""
    return HttpResponse("Trackly admin dashboard")
