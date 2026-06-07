"""
Django settings: HTTP (ASGI), Channels WebSockets, Redis sessions, Postgres.

Environment:
  DJANGO_ENV=development|production
  Optional dotenv: set DJANGO_DOTENV_FILE to a path, or a default file is loaded
  from the repo root (parent of src/) based on DJANGO_ENV before Django reads
  other variables. Existing OS environment variables win over dotenv values.
"""
import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

# src/ (contains manage.py, apps, templates)
BASE_DIR = Path(__file__).resolve().parent.parent
# monorepo/ (pyproject.toml, docker-compose, .env.*)
REPO_ROOT = BASE_DIR.parent

_DEFAULT_DEV_SECRET = "django-insecure-dev-only-change-in-production"


def _load_dotenv() -> None:
    """Load .env file into os.environ for local/proc setups (override=False: shell wins)."""
    explicit = os.environ.get("DJANGO_DOTENV_FILE", "").strip()
    if explicit:
        path = Path(explicit).expanduser()
    else:
        env_hint = os.environ.get("DJANGO_ENV", "").strip().lower()
        if env_hint == "production":
            path = REPO_ROOT / ".env.production"
        else:
            path = REPO_ROOT / ".env.development"
    if not path.is_file():
        return
    from dotenv import load_dotenv

    load_dotenv(path, override=False)


_load_dotenv()

DJANGO_ENV = os.environ.get("DJANGO_ENV", "development").strip().lower()
if DJANGO_ENV not in ("development", "production"):
    raise ImproperlyConfigured(
        f"DJANGO_ENV must be 'development' or 'production', got {DJANGO_ENV!r}."
    )

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", _DEFAULT_DEV_SECRET)
DEBUG = os.environ.get("DJANGO_DEBUG", "true").lower() in ("1", "true", "yes")

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
ALLOWED_HOSTS = [h.strip() for h in ALLOWED_HOSTS if h.strip()]

if DJANGO_ENV == "production":
    if not SECRET_KEY or SECRET_KEY == _DEFAULT_DEV_SECRET:
        raise ImproperlyConfigured(
            "Set DJANGO_SECRET_KEY to a unique, unpredictable value in production."
        )
    if DEBUG:
        raise ImproperlyConfigured("Set DJANGO_DEBUG=false in production.")
    if not ALLOWED_HOSTS:
        raise ImproperlyConfigured("Set DJANGO_ALLOWED_HOSTS in production.")

INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "channels",
    "chat",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

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

_redis_host = os.environ.get("REDIS_HOST", "127.0.0.1")
_redis_port = int(os.environ.get("REDIS_PORT", "6379"))
_redis_sessions_db = os.environ.get("REDIS_SESSIONS_DB", "1")
_redis_channels_db = os.environ.get("REDIS_CHANNELS_DB", "0")

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{_redis_host}:{_redis_port}/{_redis_sessions_db}",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    },
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [
                f"redis://{_redis_host}:{_redis_port}/{int(_redis_channels_db)}",
            ],
        },
    },
}

_pg_host = os.environ.get("POSTGRES_HOST", "127.0.0.1")
_pg_port = os.environ.get("POSTGRES_PORT", "5432")
_pg_name = os.environ.get("POSTGRES_DB", "monorepo")
_pg_user = os.environ.get("POSTGRES_USER", "monorepo")
_pg_pass = os.environ.get("POSTGRES_PASSWORD", "monorepo")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": _pg_name,
        "USER": _pg_user,
        "PASSWORD": _pg_pass,
        "HOST": _pg_host,
        "PORT": _pg_port,
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/accounts/login/"

CSRF_TRUSTED_ORIGINS = [
    o.strip()
    for o in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if o.strip()
]

# Tell Django it is behind a reverse proxy that terminates SSL
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

if DJANGO_ENV == "production":
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = os.environ.get(
        "DJANGO_SECURE_SSL_REDIRECT", "true"
    ).lower() in ("1", "true", "yes")
