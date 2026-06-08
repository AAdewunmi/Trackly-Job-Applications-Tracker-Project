"""Admin registrations for Trackly insight models."""

from django.contrib import admin

from apps.insights.models import JobInsight, TargetRoleProfile


@admin.register(TargetRoleProfile)
class TargetRoleProfileAdmin(admin.ModelAdmin):
    """Admin configuration for target role profiles."""

    list_display = ("title", "owner", "is_active", "updated_at")
    list_filter = ("is_active", "created_at", "updated_at")
    search_fields = ("title", "owner__email", "keywords")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-updated_at",)


@admin.register(JobInsight)
class JobInsightAdmin(admin.ModelAdmin):
    """Admin configuration for stored job insights."""

    list_display = (
        "job_application",
        "target_profile",
        "similarity_score",
        "score_label",
        "pipeline_version",
        "created_at",
    )
    list_filter = ("score_label", "pipeline_version", "created_at")
    search_fields = (
        "job_application__title",
        "job_application__company",
        "job_application__owner__email",
        "target_profile__title",
        "target_profile__owner__email",
        "source_hash",
    )
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)
