"""Django settings for the file sharing system."""

from datetime import timedelta
from pathlib import Path
import os
from urllib.parse import unquote


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-change-me")
DEBUG = os.getenv("DEBUG", "0") == "1"

allowed_hosts = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0")
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
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "users.middleware.JWTAuthenticationMiddleware",
    "files.middleware.SecureTokenMiddleware",
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

database_engine = os.getenv("DB_ENGINE", "django.db.backends.sqlite3")

if database_engine == "django.db.backends.sqlite3":
    DATABASES = {
        "default": {
            "ENGINE": database_engine,
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    # Prefer explicit Supabase pooler settings when they are available.
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
        # Fall back to an explicit Supabase/DATABASE_URL connection string when provided.
        supabase_url = os.getenv("SUPABASE_CONNECTION_STRING") or os.getenv("DATABASE_URL")

        if supabase_url:
            # Handle URLs where the password may contain '@' by splitting on the last '@'.
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
                    # Supabase requires SSL; ensure Django connects with sslmode=require
                    "OPTIONS": {"sslmode": "require"},
                }
            }
        else:
            DATABASES = {
                "default": {
                    "ENGINE": database_engine,
                    "NAME": os.getenv("DB_NAME", "file_sharing_system"),
                    "USER": os.getenv("DB_USER", "file_sharing_user"),
                    "PASSWORD": os.getenv("DB_PASSWORD", "file_sharing_password"),
                    "HOST": os.getenv("DB_HOST", "db"),
                    "PORT": os.getenv("DB_PORT", "5432"),
                }
            }

AUTH_USER_MODEL = "users.CustomUser"
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

# Celery/Redis settings
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

# Django cache via redis (for rate limiting / counters)
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.getenv("REDIS_URL", "redis://redis:6379/1"),
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    }
}

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

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# CORS Configuration
cors_origins = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost,http://127.0.0.1")
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]

CORS_ALLOW_CREDENTIALS = True

# Nginx/Proxy settings for production
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
TRUSTED_PROXIES = ["nginx", "127.0.0.1", "0.0.0.0"]

# Database connection pooling with PgBouncer
DATABASES["default"]["CONN_MAX_AGE"] = 600
DATABASES["default"]["OPTIONS"]["connect_timeout"] = 10

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")