"""Users application configuration."""

from django.apps import AppConfig


class UsersConfig(AppConfig):
    """Configure the users app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.users"
