"""Application configuration for the insights app."""

from django.apps import AppConfig


class InsightsConfig(AppConfig):
    """Configure the Trackly insights app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.insights"
