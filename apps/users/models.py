"""Custom user model for Trackly identity and authentication."""

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Create Trackly users with email as the primary login identifier."""

    use_in_migrations = True

    def create_user(
        self,
        email: str,
        password: str | None = None,
        **extra_fields: object,
    ) -> "User":
        """Create and save a standard user with the given email and password."""
        if not email:
            raise ValueError("Users must provide an email address.")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email: str,
        password: str | None = None,
        **extra_fields: object,
    ) -> "User":
        """Create and save a superuser with staff and superuser permissions."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superusers must have is_staff=True.")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superusers must have is_superuser=True.")

        return self.create_user(email=email, password=password, **extra_fields)


class User(AbstractUser):
    """Trackly user account using email-based authentication."""

    username = None
    email = models.EmailField(_("email address"), unique=True)
    roles = models.ManyToManyField(
        "roles.Role",
        blank=True,
        related_name="users",
        help_text="Product roles assigned to the user.",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()

    class Meta:
        """Model metadata for user ordering."""

        ordering = ["email"]

    def __str__(self) -> str:
        """Return the email address as the stable user label."""
        return self.email

    @property
    def display_name(self) -> str:
        """Return a friendly display name when available."""
        full_name = self.get_full_name().strip()

        if full_name:
            return full_name

        return self.email
