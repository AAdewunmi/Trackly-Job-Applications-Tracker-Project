"""Application configuration for the users app."""

from django.apps import AppConfig


class UsersConfig(AppConfig):
    """Configure the Trackly users app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.users"
