"""
Django application configuration for Trackly insights.
"""

from django.apps import AppConfig


class InsightsConfig(AppConfig):
    """Application configuration for the insights app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.insights"
