"""Doc2All settings.

Nothing needs a key to run on a developer's computer. Values come from environment variables, or from a
`.env` file in the project folder (ignored by git; see `.env.example`). Setting DJANGO_SECRET_KEY switches
development mode off, so a real deployment cannot run with the development defaults.
"""
import secrets
from pathlib import Path

from decouple import Config, RepositoryEmpty, RepositoryEnv

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
CONVERTER_PROFILE_DIR = config("CONVERTER_PROFILE_DIR", default="")  # LibreOffice settings folder of our own

# Django's sign-in apps are not installed yet. Add our own user model before adding them.
INSTALLED_APPS = [
    "rest_framework",
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

# SQLite while the features are built. The design uses PostgreSQL (docs/design/data-model.md).
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# JSON in and out. No sign-in yet: when accounts arrive, the default becomes "signed in only".
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [],
    "UNAUTHENTICATED_USER": None,
}

LANGUAGE_CODE = "en"
TIME_ZONE = "UTC"
USE_TZ = True
