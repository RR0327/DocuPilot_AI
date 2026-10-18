# Celery imports only when the optional async dependency is installed.
try:
    from .celery import app as celery_app
except ImportError:
    celery_app = None
__all__ = ("celery_app",)
