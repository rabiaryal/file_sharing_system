"""Django settings for the file sharing system."""

from datetime import timedelta
from pathlib import Path
import logging
import os
import structlog
from urllib.parse import unquote
from django.core.exceptions import ImproperlyConfigured


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-change-me")
DEBUG = os.getenv("DEBUG", "0") == "1"

# Detect if running on Render production vs local development
IS_PRODUCTION = os.getenv("DEBUG", "1") == "false"

allowed_hosts = os.getenv(
    "ALLOWED_HOSTS",
    "localhost,127.0.0.1,0.0.0.0,file-sharing-api-latest-r939.onrender.com,share-file.rabiaryal.com.np,www.share-file.rabiaryal.com.np",
)
ALLOWED_HOSTS = [host.strip() for host in allowed_hosts.split(",") if host.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "users.apps.UsersConfig",
    "files",
    "drf_spectacular",
    "django_structlog",   # ← added
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "users.middleware.JWTAuthenticationMiddleware",
    "files.middleware.SecureTokenMiddleware",
    "django_structlog.middlewares.RequestMiddleware",   # ← added (after AuthenticationMiddleware)
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"

# =====================================================================
# DATABASE
# =====================================================================
# =====================================================================
# DATABASE
# =====================================================================
supabase_host = os.getenv("SUPABASE_HOST")
supabase_port = os.getenv("SUPABASE_PORT")
supabase_name = os.getenv("SUPABASE_DATABASE")
supabase_user = os.getenv("SUPABASE_USER")
supabase_password = os.getenv("SUPABASE_PASSWORD")

if supabase_host and supabase_port and supabase_name and supabase_user and supabase_password:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": supabase_name,
            "USER": supabase_user,
            "PASSWORD": supabase_password,
            "HOST": supabase_host,
            "PORT": supabase_port,
            "OPTIONS": {"sslmode": "require"},
        }
    }
else:
    supabase_url = os.getenv("SUPABASE_CONNECTION_STRING") or os.getenv("DATABASE_URL")

    if not supabase_url:
        raise ImproperlyConfigured(
            "No database configuration found. Set either SUPABASE_HOST/PORT/DATABASE/USER/PASSWORD "
            "or SUPABASE_CONNECTION_STRING / DATABASE_URL."
        )

    url = supabase_url
    if "://" in url:
        _, rest = url.split("://", 1)
    else:
        rest = url

    if "@" in rest:
        creds, host_rest = rest.rsplit("@", 1)
        if ":" in creds:
            user, password = creds.split(":", 1)
            user = unquote(user)
            password = unquote(password)
        else:
            user = creds
            password = ""
    else:
        host_rest = rest
        user = os.getenv("DB_USER", "file_sharing_user")
        password = os.getenv("DB_PASSWORD", "file_sharing_password")

    if "/" in host_rest:
        hostport, dbname = host_rest.split("/", 1)
    else:
        hostport = host_rest
        dbname = os.getenv("DB_NAME", "file_sharing_system")

    if ":" in hostport:
        host, port = hostport.rsplit(":", 1)
    else:
        host = hostport
        port = os.getenv("DB_PORT", "5432")

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": dbname,
            "USER": user,
            "PASSWORD": password,
            "HOST": host,
            "PORT": port,
            "OPTIONS": {"sslmode": "require"},
        }
    }

DATABASES["default"]["CONN_MAX_AGE"] = 600
DATABASES["default"].setdefault("OPTIONS", {})["connect_timeout"] = 10
# =====================================================================
# AUTH
# =====================================================================
AUTH_USER_MODEL = "users.CustomUser"
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

# =====================================================================
# REST FRAMEWORK
# =====================================================================
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "core.exception_handler.global_api_exception_handler",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

# =====================================================================
# CELERY
# =====================================================================
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
CELERY_LOG_LEVEL = "info"

if CELERY_BROKER_URL.startswith("rediss://"):
    CELERY_BROKER_TRANSPORT_OPTIONS = {
        "connection_class": "redis.SSLConnection",
    }
    CELERY_REDIS_BACKEND_USE_SSL = {
        "ssl_cert_reqs": None
    }
# =====================================================================
# CACHE
# =====================================================================
_REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/1")
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": _REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            **(
                {"CONNECTION_POOL_KWARGS": {"ssl_cert_reqs": None}}
                if _REDIS_URL.startswith("rediss://")
                else {}
            ),
        },
    }
}

# =====================================================================
# SPECTACULAR (API DOCS)
# =====================================================================
SPECTACULAR_SETTINGS = {
    "TITLE": "File Sharing System API",
    "DESCRIPTION": "API documentation for the file sharing system.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENTS": {
        "securitySchemes": {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            }
        }
    },
    "SECURITY": [{"BearerAuth": []}],
}

# =====================================================================
# INTERNATIONALISATION
# =====================================================================
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# =====================================================================
# STATIC / MEDIA
# =====================================================================
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =====================================================================
# CORS / CSRF
# =====================================================================
cors_origins = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "https://share-file.rabiaryal.com.np,https://www.share-file.rabiaryal.com.np,http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://localhost,http://127.0.0.1",
)
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]
CORS_ALLOW_CREDENTIALS = True

csrf_trusted_origins = os.getenv(
    "CSRF_TRUSTED_ORIGINS",
    "https://share-file.rabiaryal.com.np,https://www.share-file.rabiaryal.com.np,https://file-sharing-api-latest-r939.onrender.com",
)
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in csrf_trusted_origins.split(",") if origin.strip()]

# =====================================================================
# PROXY / HTTPS
# =====================================================================
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
TRUSTED_PROXIES = ["nginx", "127.0.0.1", "0.0.0.0"]
ACCOUNT_DEFAULT_HTTP_PROTOCOL = os.getenv("ACCOUNT_DEFAULT_HTTP_PROTOCOL", "https")
SOCIAL_AUTH_REDIRECT_IS_HTTPS = os.getenv("SOCIAL_AUTH_REDIRECT_IS_HTTPS", "1") == "1"
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "0") == "1"

# =====================================================================
# GOOGLE OAUTH
# =====================================================================
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

# =====================================================================
# MONGODB LOGGING — env vars (read by core/log_worker.py)
# =====================================================================
# These are read directly by log_worker.py via os.getenv().
# Defining them here as well for documentation clarity.
# MONGO_URI            = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
# MONGO_LOG_DB         = os.getenv("MONGO_LOG_DB", "file_sharing_logs")
# MONGO_LOG_COLLECTION = os.getenv("MONGO_LOG_COLLECTION", "logs")
# LOG_QUEUE_MAX        = os.getenv("LOG_QUEUE_MAX", "10000")
# LOG_BATCH_SIZE       = os.getenv("LOG_BATCH_SIZE", "50")
# LOG_FLUSH_INTERVAL   = os.getenv("LOG_FLUSH_INTERVAL", "2.0")
# LOG_TTL_SECONDS      = os.getenv("LOG_TTL_SECONDS", "2592000")  # 30 days

# =====================================================================
# DJANGO-STRUCTLOG
# =====================================================================
DJANGO_STRUCTLOG_COMMAND_FAILED_AS_ERROR = True

# =====================================================================
# STDLIB LOGGING — keeps Django's own internal logs working
# =====================================================================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        # Silence the mongo log worker's own fallback logger below WARNING
        "log_worker": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}

# =====================================================================
# STRUCTLOG CONFIGURATION
# =====================================================================
# Deferred import wrapper — AsyncMongoProcessor lives in core/log_processor.py
# but Django apps aren't ready when settings.py is first loaded, so we
# defer the actual import until the first log call.
class _DeferredMongoProcessor:
    _instance = None

    def __call__(self, logger, method, event_dict):
        if self._instance is None:
            from logger.log_processor import AsyncMongoProcessor
            self._instance = AsyncMongoProcessor()
        return self._instance(logger, method, event_dict)


_shared_processors = [
    # Merges request_id, user_id bound by django-structlog RequestMiddleware
    structlog.contextvars.merge_contextvars,
    structlog.processors.add_log_level,
    structlog.processors.TimeStamper(fmt="iso", utc=True),
    structlog.processors.StackInfoRenderer(),
    structlog.processors.format_exc_info,
]

# Dev → colored terminal output. Prod → JSON (one line per event).
_renderer = (
    structlog.dev.ConsoleRenderer(colors=True)
    if DEBUG
    else structlog.processors.JSONRenderer()
)

structlog.configure(
    processors=[
        *_shared_processors,
        _DeferredMongoProcessor(),  # enqueues to background worker, passes through
        _renderer,
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)