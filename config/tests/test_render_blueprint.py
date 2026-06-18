"""Tests for the Render deployment blueprint contract."""

from pathlib import Path

RENDER_BLUEPRINT = Path(__file__).resolve().parents[2] / "render.yaml"


def test_render_blueprint_defines_trackly_web_service() -> None:
    """The Render blueprint should define the expected web service contract."""
    content = RENDER_BLUEPRINT.read_text(encoding="utf-8")

    assert "name: trackly-web" in content
    assert "runtime: docker" in content
    assert "dockerfilePath: ./Dockerfile" in content
    assert "dockerContext: ." in content
    assert "gunicorn config.wsgi:application" in content
    assert "healthCheckPath: /health/" in content


def test_render_blueprint_runs_production_startup_steps() -> None:
    """Render startup should migrate, collect static files, and start Gunicorn."""
    content = RENDER_BLUEPRINT.read_text(encoding="utf-8")

    assert "python manage.py migrate --noinput" in content
    assert "--settings=config.settings.production" in content
    assert "python manage.py collectstatic --noinput" in content
    assert "--bind 0.0.0.0:$PORT" in content


def test_render_blueprint_wires_database_and_required_environment() -> None:
    """Render should wire PostgreSQL and production environment variables."""
    content = RENDER_BLUEPRINT.read_text(encoding="utf-8")

    assert "name: trackly-db" in content
    assert "databaseName: trackly" in content
    assert "user: trackly_user" in content
    assert "key: DATABASE_URL" in content
    assert "fromDatabase:" in content
    assert "property: connectionString" in content
    assert "key: DJANGO_SETTINGS_MODULE" in content
    assert "value: config.settings.production" in content
    assert "key: DJANGO_SECRET_KEY" in content
    assert "generateValue: true" in content
    assert "key: DJANGO_ALLOWED_HOSTS" in content
    assert "value: .onrender.com" in content
    assert "key: DJANGO_CSRF_TRUSTED_ORIGINS" in content
    assert "value: https://*.onrender.com" in content
