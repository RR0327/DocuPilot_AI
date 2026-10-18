"""Deterministic deployment gate; refuses insecure non-debug configuration."""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.checks import run_checks
from pathlib import Path

class Command(BaseCommand):
    help = "Check DocuPilot deployment-security baseline and local dependencies (read-only)."

    def handle(self, *args, **options):
        failures = []
        if run_checks():
            failures.append("Django system checks reported problems")
        if settings.DATABASES["default"]["ENGINE"] != "django.db.backends.sqlite3":
            failures.append("This release requires SQLite3")
        if getattr(settings, "MEDIA_URL", None):
            failures.append("Private documents must not have a public MEDIA_URL")
        if not settings.DEBUG:
            if "rest_framework.authentication.BasicAuthentication" in settings.REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"]:
                failures.append("Production Basic authentication is forbidden; session-only required")
            if settings.DOCUPILOT_LOGIN_FAILURE_LIMIT > 10:
                failures.append("Login failure limit is too permissive")
            if settings.DOCUPILOT_SESSION_IDLE_SECONDS > settings.SESSION_COOKIE_AGE:
                failures.append("Idle timeout must not exceed session lifetime")
            if not settings.SECURE_SSL_REDIRECT:
                failures.append("Enable HTTPS redirect behind a correctly configured TLS endpoint")
            if not settings.SESSION_COOKIE_SECURE or not settings.CSRF_COOKIE_SECURE:
                failures.append("Secure session/CSRF cookies required")
            if settings.SECRET_KEY in ("development-only-not-for-production", "replace-with-a-long-random-value") or len(settings.SECRET_KEY) < 50:
                failures.append("Replace insecure secret key")
            if "*" in settings.ALLOWED_HOSTS or not settings.ALLOWED_HOSTS:
                failures.append("Use a restricted ALLOWED_HOSTS list")
            if settings.SECURE_HSTS_SECONDS == 0:
                self.stdout.write(self.style.WARNING("HSTS not enabled: configure after validating HTTPS on production domain"))
        else:
            self.stdout.write(self.style.WARNING("DEBUG=true: local development assessment only, NOT production approved"))
        if settings.DATABASES["default"]["NAME"] == ":memory:":
            failures.append("In-memory database is not appropriate for a persistent installation")
        if failures:
            raise CommandError("Release gate failed: " + "; ".join(failures))
        self.stdout.write(self.style.SUCCESS("Release configuration checks passed (not a penetration test or deployment approval)"))
