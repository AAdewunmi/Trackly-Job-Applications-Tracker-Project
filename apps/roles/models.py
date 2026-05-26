"""Role models for Trackly access-control foundations."""

from django.db import models


class Role(models.Model):
    """Represent a product role assignable to Trackly users."""

    class Codes(models.TextChoices):
        """Supported role codes for Sprint 1 product access."""

        ADMIN = "admin", "Admin"
        MEMBER = "member", "Member"

    code = models.CharField(max_length=50, unique=True, choices=Codes.choices)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Model metadata for role ordering."""

        ordering = ["code"]

    def __str__(self) -> str:
        """Return the human-readable role name."""
        return self.name
