"""Tests for Trackly error page templates."""

from django.template.loader import render_to_string


def test_not_found_template_renders_trackly_error_page() -> None:
    """The 404 template should render a branded recovery path."""
    content = render_to_string("404.html")

    assert "Page not found" in content
    assert "Go home" in content
    assert "Open applications" in content


def test_permission_denied_template_renders_trackly_error_page() -> None:
    """The 403 template should render a branded access-control message."""
    content = render_to_string("403.html")

    assert "Access restricted" in content
    assert "403" in content
    assert "Sign in" in content


def test_server_error_template_renders_without_request_context() -> None:
    """Django's default 500 handler renders without normal request context."""
    content = render_to_string("500.html")

    assert "Something went wrong" in content
    assert "500" in content
    assert "Go home" in content
