#!/usr/bin/env python
import os
import sys
from pathlib import Path

# Ensure the project root is on Python path so imports like
# "import sms_project" work when the environment doesn't
# automatically add the script directory to sys.path (e.g. Vercel).
PROJECT_ROOT = str(Path(__file__).resolve().parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sms_project.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
