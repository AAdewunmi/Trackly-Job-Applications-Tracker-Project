"""User account views."""

from django.http import HttpRequest, HttpResponse


def profile(request: HttpRequest) -> HttpResponse:
    """Render the user profile placeholder."""
    return HttpResponse("Trackly profile")
