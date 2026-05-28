"""Django application configuration for the jobs app."""

from django.apps import AppConfig


class JobsConfig(AppConfig):
    """Application configuration for job tracking domain behaviour."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.jobs"
    verbose_name = "Jobs"
