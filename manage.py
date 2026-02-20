#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

import spi_config


def main():
    config = spi_config.get_config()
    os.environ["DJANGO_SETTINGS_MODULE"] = config["django"]["settings_module"]

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
