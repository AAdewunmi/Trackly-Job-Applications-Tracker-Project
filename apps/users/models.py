"""User models for Trackly."""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Email-first Trackly user."""

    username = None
    email = models.EmailField(unique=True)
    roles = models.ManyToManyField("roles.Role", blank=True, related_name="users")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self) -> str:
        return self.email
