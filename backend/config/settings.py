"""Doc2All settings.

Nothing needs a key to run on a developer's computer. Values come from environment variables, or from a
`.env` file in the project folder (ignored by git; see `.env.example`). Setting DJANGO_SECRET_KEY switches
development mode off, so a real deployment cannot run with the development defaults.
"""
import secrets
from pathlib import Path

from decouple import Config, RepositoryEmpty, RepositoryEnv
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR.parent / ".env"
config = Config(RepositoryEnv(ENV_FILE) if ENV_FILE.is_file() else RepositoryEmpty())

SECRET_KEY = config("DJANGO_SECRET_KEY", default="")
DEBUG = not SECRET_KEY
if DEBUG:
    SECRET_KEY = secrets.token_urlsafe(50)  # new at every start, never written down

ALLOWED_HOSTS = [host for host in config("DJANGO_ALLOWED_HOSTS", default="localhost,127.0.0.1").split(",") if host]

# The processing programs. Empty means: find them (PATH, then the usual Windows place).
SOFFICE_PATH = config("SOFFICE_PATH", default="")  # LibreOffice
TESSERACT_PATH = config("TESSERACT_PATH", default="")
TESSDATA_DIR = config("TESSDATA_DIR", default="")  # folder with the Tesseract language files (eng, fra, ...)
CONVERTER_TIMEOUT = config("CONVERTER_TIMEOUT", default=60, cast=int)  # seconds one job may take (SR-12)
CONVERTER_WORKDIR = config("CONVERTER_WORKDIR", default="")  # where temporary files go; empty = system temp folder
CONVERTER_MEMORY_MB = config("CONVERTER_MEMORY_MB", default=1024, cast=int)  # memory one program may take (SR-12)


def _local_key(path):
    """On a developer's computer: a key made once and kept in a file that git ignores."""
    if not path.is_file():
        path.write_text(secrets.token_hex(32), encoding="ascii")
    return path.read_text(encoding="ascii").strip()


# The secret behind the audit log fingerprints. It must stay the same from one start to the next.
AUDIT_KEY = config("AUDIT_KEY", default="") or (_local_key(BASE_DIR / "audit.key") if DEBUG else "")
if not AUDIT_KEY:
    raise ImproperlyConfigured("Set AUDIT_KEY.")

# Django's sign-in apps are not installed yet. Add our own user model before adding them.
INSTALLED_APPS = [
    "rest_framework",
    "core",
    "files",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "core.limits.RequestSize",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

# SQLite while the features are built. The design uses PostgreSQL (docs/design/data-model.md).
DATABASES = {"default": {
    "ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3",
    # jobs write from their own threads: wait for each other instead of failing
    "OPTIONS": {"timeout": 20, "transaction_mode": "IMMEDIATE", "init_command": "PRAGMA journal_mode=WAL;"},
}}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# JSON in and out. No sign-in yet: when accounts arrive, the default becomes "signed in only".
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["core.csrf.FormToken"],
    "UNAUTHENTICATED_USER": None,
    "EXCEPTION_HANDLER": "core.errors.handler",
}

# Uploaded files and results: a private folder (ignored by git) that nothing serves directly (SR-10).
PRIVATE_FILES_DIR = Path(config("PRIVATE_FILES_DIR", default=str(BASE_DIR / "private_files")))
MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # SR-09
MAX_PAGES = 100  # SR-09
UPLOADS_PER_HOUR = 20  # SR-09
MAX_ACTIVE_JOBS = 5  # jobs waiting or running at the same time (AC-09)
MAX_EXPANSION = 100  # SR-14: refused when it grows more than this many times,
MAX_EXPANDED_BYTES = 500 * 1024 * 1024  # or beyond this size
DATA_UPLOAD_MAX_NUMBER_FILES = 1

# Browser protections (SR-21). The ones that need HTTPS are on outside development.
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Strict"
SECURE_REFERRER_POLICY = "no-referrer"
X_FRAME_OPTIONS = "DENY"
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
JOBS_INLINE = False  # tests run jobs at once instead of in the background

LANGUAGE_CODE = "en"
TIME_ZONE = "UTC"
USE_TZ = True
