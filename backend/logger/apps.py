"""
apps.py
-------
Starts the background log worker once when Django is fully initialised.

Django calls AppConfig.ready() once per process after all models are loaded.
The RUN_MAIN guard prevents double-start during the autoreloader fork.
"""

import os
from django.apps import AppConfig


class LoggerConfig(AppConfig):
    name = "logger"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        if os.environ.get("RUN_MAIN") == "true" or os.environ.get("DJANGO_SETTINGS_MODULE"):
            from .log_worker import start_log_worker
            start_log_worker()