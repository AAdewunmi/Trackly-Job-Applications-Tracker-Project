"""Tests for production settings environment contracts."""

import importlib
import sys

import pytest
from django.core.exceptions import ImproperlyConfigured

PRODUCTION_SETTINGS_MODULE = "config.settings.production"


def import_production_settings():
    """Import production settings after clearing any cached module state."""
    sys.modules.pop(PRODUCTION_SETTINGS_MODULE, None)
    settings_package = sys.modules.get("config.settings")

    if settings_package is not None and hasattr(settings_package, "production"):
        delattr(settings_package, "production")

    return importlib.import_module(PRODUCTION_SETTINGS_MODULE)


@pytest.fixture(autouse=True)
def clear_production_settings_module():
    """Keep production settings imports isolated across tests."""
    sys.modules.pop(PRODUCTION_SETTINGS_MODULE, None)
    yield
    sys.modules.pop(PRODUCTION_SETTINGS_MODULE, None)


def test_production_settings_load_from_required_environment(monkeypatch) -> None:
    """Production settings should load required runtime values from env."""
    monkeypatch.setenv("DJANGO_SECRET_KEY", "production-secret")
    monkeypatch.setenv("DJANGO_ALLOWED_HOSTS", "trackly.example.com,www.example.com")
    monkeypatch.setenv("RELEASE_VERSION", "test-release")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    monkeypatch.setenv("DJANGO_LOG_LEVEL", "ERROR")
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgres://trackly_user:trackly_password@db.example.com:5432/trackly_prod",
    )

    settings = import_production_settings()

    assert settings.DEBUG is False
    assert settings.SECRET_KEY == "production-secret"
    assert settings.ALLOWED_HOSTS == ["trackly.example.com", "www.example.com"]
    assert settings.DATABASES["default"]["HOST"] == "db.example.com"
    assert settings.DATABASES["default"]["NAME"] == "trackly_prod"
    assert settings.DATABASES["default"]["USER"] == "trackly_user"
    assert settings.SECURE_SSL_REDIRECT is True
    assert settings.SESSION_COOKIE_SECURE is True
    assert settings.CSRF_COOKIE_SECURE is True
    assert settings.SECURE_HSTS_SECONDS == 31536000
    assert settings.SECURE_HSTS_INCLUDE_SUBDOMAINS is True
    assert settings.SECURE_HSTS_PRELOAD is True
    assert settings.STATICFILES_STORAGE == (
        "whitenoise.storage.CompressedManifestStaticFilesStorage"
    )
    assert settings.RELEASE_VERSION == "test-release"
    assert settings.LOGGING["root"]["level"] == "WARNING"
    assert settings.LOGGING["loggers"]["django"]["level"] == "ERROR"
    assert (
        "release=%(release_version)s"
        in settings.LOGGING["formatters"]["standard"]["format"]
    )
    assert settings.LOGGING["handlers"]["console"]["filters"] == ["release_version"]


def test_release_version_filter_adds_release_metadata(monkeypatch) -> None:
    """Production logging should attach release metadata to each record."""
    monkeypatch.setenv("DJANGO_SECRET_KEY", "production-secret")
    monkeypatch.setenv("DJANGO_ALLOWED_HOSTS", "trackly.example.com")
    monkeypatch.setenv("RELEASE_VERSION", "test-release")
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgres://trackly_user:trackly_password@db.example.com:5432/trackly_prod",
    )

    settings = import_production_settings()

    class LogRecord:
        pass

    record = LogRecord()
    assert settings.ReleaseVersionFilter().filter(record) is True
    assert record.release_version == "test-release"


def test_production_settings_require_secret_key(monkeypatch) -> None:
    """Production settings should fail fast when the secret is missing."""
    monkeypatch.delenv("DJANGO_SECRET_KEY", raising=False)
    monkeypatch.setenv("DJANGO_ALLOWED_HOSTS", "trackly.example.com")
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgres://trackly_user:trackly_password@db.example.com:5432/trackly_prod",
    )

    with pytest.raises(KeyError, match="DJANGO_SECRET_KEY"):
        import_production_settings()


@pytest.mark.parametrize("hosts", [None, ""])
def test_production_settings_require_allowed_hosts(monkeypatch, hosts) -> None:
    """Production settings should fail fast when allowed hosts are empty."""
    monkeypatch.setenv("DJANGO_SECRET_KEY", "production-secret")
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgres://trackly_user:trackly_password@db.example.com:5432/trackly_prod",
    )

    if hosts is None:
        monkeypatch.delenv("DJANGO_ALLOWED_HOSTS", raising=False)
    else:
        monkeypatch.setenv("DJANGO_ALLOWED_HOSTS", hosts)

    with pytest.raises(ImproperlyConfigured, match="DJANGO_ALLOWED_HOSTS"):
        import_production_settings()


def test_production_settings_require_database_url(monkeypatch) -> None:
    """Production settings should fail fast when the database URL is missing."""
    monkeypatch.setenv("DJANGO_SECRET_KEY", "production-secret")
    monkeypatch.setenv("DJANGO_ALLOWED_HOSTS", "trackly.example.com")
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(KeyError, match="DATABASE_URL"):
        import_production_settings()
