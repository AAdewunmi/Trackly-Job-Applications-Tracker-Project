"""Admin registrations for Trackly job application models."""

from django.contrib import admin

from apps.jobs.models import ApplicationNote, JobApplication


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    """Admin configuration for user-owned job applications."""

    list_display = (
        "title",
        "company",
        "owner",
        "status",
        "applied_date",
        "updated_at",
    )
    list_filter = ("status", "applied_date", "created_at")
    search_fields = ("title", "company", "owner__email")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-updated_at",)


@admin.register(ApplicationNote)
class ApplicationNoteAdmin(admin.ModelAdmin):
    """Admin configuration for application notes."""

    list_display = ("application", "owner_email", "created_at")
    search_fields = (
        "application__title",
        "application__company",
        "application__owner__email",
        "body",
    )
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)

    def owner_email(self, obj: ApplicationNote) -> str:
        """Return the owning user's email address for list display."""
        return obj.owner.email

    owner_email.short_description = "Owner email"
