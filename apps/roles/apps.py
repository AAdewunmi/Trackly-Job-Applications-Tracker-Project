"""Application configuration for the roles app."""

from django.apps import AppConfig


class RolesConfig(AppConfig):
    """Configure the Trackly roles app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.roles"
