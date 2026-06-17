"""Production settings for Trackly."""

import os

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = False

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", default=[])  # noqa: F405
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS is required in production.")

CSRF_TRUSTED_ORIGINS = env_list(  # noqa: F405
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    default=[],
)

DATABASES = {  # noqa: F405
    "default": dj_database_url.config(
        default=os.environ["DATABASE_URL"],
        conn_max_age=600,
        conn_health_checks=True,
    )
}

SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", default=True)  # noqa: F405
SESSION_COOKIE_SECURE = env_bool(  # noqa: F405
    "DJANGO_SESSION_COOKIE_SECURE", default=True
)
CSRF_COOKIE_SECURE = env_bool("DJANGO_CSRF_COOKIE_SECURE", default=True)  # noqa: F405
SECURE_HSTS_SECONDS = env_int(  # noqa: F405
    "DJANGO_SECURE_HSTS_SECONDS", default=31536000
)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool(  # noqa: F405
    "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS",
    default=True,
)
SECURE_HSTS_PRELOAD = env_bool("DJANGO_SECURE_HSTS_PRELOAD", default=True)  # noqa: F405
SECURE_CONTENT_TYPE_NOSNIFF = env_bool(  # noqa: F405
    "DJANGO_SECURE_CONTENT_TYPE_NOSNIFF",
    default=True,
)
X_FRAME_OPTIONS = env_str("DJANGO_X_FRAME_OPTIONS", default="DENY")  # noqa: F405
SECURE_REFERRER_POLICY = env_str(  # noqa: F405
    "DJANGO_REFERRER_POLICY",
    default="same-origin",
)

RELEASE_VERSION = env_str("RELEASE_VERSION", default="production")  # noqa: F405

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": (
                "%(levelname)s %(asctime)s %(name)s "
                "%(module)s %(process)d %(thread)d %(message)s"
            ),
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": env_str("LOG_LEVEL", default="INFO"),  # noqa: F405
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": env_str("DJANGO_LOG_LEVEL", default="INFO"),  # noqa: F405
            "propagate": False,
        },
    },
}
