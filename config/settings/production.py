"""Production settings for Trackly."""

from .base import *  # noqa: F403

DEBUG = env_bool("DJANGO_DEBUG", default=False)  # noqa: F405

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
REFERRER_POLICY = env_str("DJANGO_REFERRER_POLICY", default="same-origin")  # noqa: F405

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
        "level": "INFO",
    },
}
