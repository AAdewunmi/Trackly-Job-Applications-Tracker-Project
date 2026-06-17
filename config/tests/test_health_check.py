"""Tests for the operational health endpoint."""

from datetime import datetime

from django.urls import reverse


def test_health_check_returns_ok_status(client, monkeypatch) -> None:
    """The health endpoint returns a successful operational response."""
    monkeypatch.setenv("RELEASE_VERSION", "test-release")

    response = client.get(reverse("health_check"))

    assert response.status_code == 200
    assert response["Content-Type"] == "application/json"
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "trackly"


def test_health_check_includes_release_and_timestamp(client, monkeypatch) -> None:
    """The health response includes release metadata for deployment checks."""
    monkeypatch.setenv("RELEASE_VERSION", "test-release")

    response = client.get(reverse("health_check"))

    payload = response.json()
    assert payload["release"] == "test-release"
    assert "timestamp" in payload

    timestamp = datetime.fromisoformat(payload["timestamp"])
    assert timestamp.tzinfo is not None
