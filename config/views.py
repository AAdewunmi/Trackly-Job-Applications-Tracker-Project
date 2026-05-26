"""Project-level views for Trackly."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def home(request: HttpRequest) -> HttpResponse:
    """Render the public Trackly landing page."""
    return render(request, "home.html")
