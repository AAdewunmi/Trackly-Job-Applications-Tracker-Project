"""Tests for the operational health endpoint."""

from datetime import datetime

from django.urls import reverse


def test_health_check_returns_operational_metadata(client, monkeypatch) -> None:
    """The health endpoint should expose lightweight deployment metadata."""
    monkeypatch.setenv("RELEASE_VERSION", "test-release")

    response = client.get(reverse("health_check"))

    assert response.status_code == 200
    assert response["Content-Type"] == "application/json"

    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "trackly"
    assert payload["release"] == "test-release"

    timestamp = datetime.fromisoformat(payload["timestamp"])
    assert timestamp.tzinfo is not None
