#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os
import sys


def main() -> None:
	try:
		from dotenv import load_dotenv
		import pathlib
		current_path = pathlib.Path(__file__).parent.resolve()
		load_dotenv(dotenv_path=current_path / '.env')
	except ImportError:
		pass
	os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
	from django.core.management import execute_from_command_line

	execute_from_command_line(sys.argv)


if __name__ == "__main__":
	main()
