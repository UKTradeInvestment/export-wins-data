#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "data.settings_test")
        print("testing with settings: {}".format(os.environ.get("DJANGO_SETTINGS_MODULE")))
    else:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "data.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
