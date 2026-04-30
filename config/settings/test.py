"""Test settings for Trackly."""

from .base import *  # noqa: F403


DEBUG = False

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Tests should run quickly while still using the same PostgreSQL engine as local
# development. Django creates and destroys the isolated test database.
DATABASES["default"]["TEST"] = {  # noqa: F405
    "NAME": "test_trackly",
}
