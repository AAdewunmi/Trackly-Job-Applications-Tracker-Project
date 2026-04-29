
## `manage.py`

"""Command-line utility for administrative Django tasks."""

import os
import sys


def main() -> None:
    """Run Django's command-line management utility."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django could not be imported. Confirm dependencies are installed "
            "and the virtual environment or container is active."
        ) from exc

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()