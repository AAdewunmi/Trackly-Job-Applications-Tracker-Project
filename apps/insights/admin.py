"""
Django admin registrations for Trackly insights.
"""

from django.contrib import admin

from apps.insights.models import JobInsight, TargetRoleProfile


@admin.register(TargetRoleProfile)
class TargetRoleProfileAdmin(admin.ModelAdmin):
    """Admin configuration for target role profiles."""

    list_display = ["title", "owner", "is_active", "updated_at"]
    list_filter = ["is_active", "created_at", "updated_at"]
    search_fields = ["title", "owner__email", "keywords"]


@admin.register(JobInsight)
class JobInsightAdmin(admin.ModelAdmin):
    """Admin configuration for stored job insights."""

    list_display = [
        "job_application",
        "target_profile",
        "similarity_score",
        "score_label",
        "pipeline_version",
        "created_at",
    ]
    list_filter = ["score_label", "pipeline_version", "created_at"]
    search_fields = [
        "job_application__title",
        "job_application__company",
        "target_profile__title",
        "source_hash",
    ]
