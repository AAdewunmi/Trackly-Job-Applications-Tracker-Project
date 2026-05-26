"""Admin registration for Trackly roles."""

from django.contrib import admin

from apps.roles.models import Role


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Admin configuration for Role records."""

    list_display = ("code", "name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("code", "name", "description")
    ordering = ("code",)
