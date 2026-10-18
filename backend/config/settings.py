import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR.parent / ".env")
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "development-only-not-for-production")
DEBUG = os.getenv("DJANGO_DEBUG", "false").lower() == "true"
ALLOWED_HOSTS = [h.strip() for h in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]
if not DEBUG and SECRET_KEY == "development-only-not-for-production":
    raise RuntimeError("Set DJANGO_SECRET_KEY before running outside development")
INSTALLED_APPS = ["django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes", "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles", "rest_framework", "core"]
MIDDLEWARE = ["django.middleware.security.SecurityMiddleware", "django.contrib.sessions.middleware.SessionMiddleware", "django.middleware.common.CommonMiddleware", "django.middleware.csrf.CsrfViewMiddleware", "django.contrib.auth.middleware.AuthenticationMiddleware", "django.contrib.messages.middleware.MessageMiddleware", "django.middleware.clickjacking.XFrameOptionsMiddleware"]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [], "APP_DIRS": True, "OPTIONS": {"context_processors": ["django.template.context_processors.debug", "django.template.context_processors.request", "django.contrib.auth.context_processors.auth", "django.contrib.messages.context_processors.messages"]}}]
WSGI_APPLICATION = "config.wsgi.application"

# Django's built-in SQLite database: no external database service required.
# The database file is local, gitignored and created automatically by migrate.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication", "rest_framework.authentication.BasicAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}
AUTH_PASSWORD_VALIDATORS = []
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_TZ = True
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

DOCUPILOT_TESSERACT_CMD = os.getenv("DOCUPILOT_TESSERACT_CMD", "")
DOCUPILOT_OCR_LANG = os.getenv("DOCUPILOT_OCR_LANG", "eng")

# Documents are intentionally private: do not expose MEDIA_URL or serve this root.
MEDIA_ROOT = BASE_DIR / "private_media"
DATA_UPLOAD_MAX_MEMORY_SIZE = 12 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024

# Optional multilingual CPU embeddings; keyword mode works without this dependency.
DOCUPILOT_EMBEDDING_MODEL = os.getenv("DOCUPILOT_EMBEDDING_MODEL", "intfloat/multilingual-e5-small")
DOCUPILOT_MODEL_OFFLINE = os.getenv("DOCUPILOT_MODEL_OFFLINE", "false").lower() == "true"
DOCUPILOT_SEMANTIC_MIN_SCORE = float(os.getenv("DOCUPILOT_SEMANTIC_MIN_SCORE", "0.40"))

# Optional asynchronous extraction, disabled by default to keep a simple local MVP.
DOCUPILOT_ASYNC_ENABLED = os.getenv("DOCUPILOT_ASYNC_ENABLED", "false").lower() == "true"
CELERY_BROKER_URL = os.getenv("DOCUPILOT_REDIS_URL", "redis://127.0.0.1:6379/0")
CELERY_RESULT_BACKEND = None  # Job state stored in owner-scoped SQLite records.
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_TRACK_STARTED = False
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# Recovery thresholds are intentionally conservative for long-running OCR.
DOCUPILOT_STALE_QUEUE_MINUTES = int(os.getenv("DOCUPILOT_STALE_QUEUE_MINUTES", "30"))
DOCUPILOT_STALE_RUNNING_MINUTES = int(os.getenv("DOCUPILOT_STALE_RUNNING_MINUTES", "120"))
