"""Read-only, machine-readable local release gate. Never exposes secrets or private data."""
import json
from io import StringIO
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connections
from django.db.migrations.executor import MigrationExecutor
from django.urls import resolve, Resolver404

REQUIRED_ROUTES = (
    "/api/auth/csrf/", "/api/auth/login/", "/api/auth/me/", "/api/auth/logout/",
    "/api/documents/", "/api/documents/upload/", "/api/invoices/analytics/",
    "/api/classification/reliability/", "/api/classification/feedback-quality/",
    "/api/processing-jobs/overview/", "/api/reviews/",
)

def assess():
    """Return a deterministic report without reading document contents."""
    checks = {}
    def put(name, passed, explanation):
        checks[name] = {"passed": bool(passed), "detail": explanation}
    put("database_engine", settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3", "SQLite3 only")
    put("private_media", not bool(getattr(settings, "MEDIA_URL", None)), "No public media URL")
    authenticators = settings.REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"]
    put("session_auth", "rest_framework.authentication.SessionAuthentication" in authenticators, "Session authentication enabled")
    put("basic_auth_disabled", "rest_framework.authentication.BasicAuthentication" not in authenticators, "No Basic authentication in effective configuration")
    put("idle_timeout", 0 < settings.DOCUPILOT_SESSION_IDLE_SECONDS <= settings.SESSION_COOKIE_AGE, "Idle timeout within session lifetime")
    put("rate_limit", 2 <= settings.DOCUPILOT_LOGIN_FAILURE_LIMIT <= 10, "Bounded login attempt threshold")
    put("csrf_middleware", "django.middleware.csrf.CsrfViewMiddleware" in settings.MIDDLEWARE, "CSRF middleware installed")
    put("session_idle_middleware", "core.session_middleware.SessionIdleMiddleware" in settings.MIDDLEWARE, "Idle expiry for API")
    put("https_and_cookies", bool(settings.DEBUG) or (settings.SECURE_SSL_REDIRECT and settings.SESSION_COOKIE_SECURE and settings.CSRF_COOKIE_SECURE), "HTTPS redirect and secure cookies outside debug")
    put("host_restriction", bool(settings.ALLOWED_HOSTS) and "*" not in settings.ALLOWED_HOSTS, "Restricted ALLOWED_HOSTS")
    for endpoint in REQUIRED_ROUTES:
        try:
            resolve(endpoint)
            present = True
        except Resolver404:
            present = False
        put("route_" + endpoint.strip('/').replace('/','_').replace('-','_'), present, "Required API route resolves")
    return checks

class Command(BaseCommand):
    help = "Read-only Phase 5 acceptance checks; JSON report omits secrets, users and documents."

    def add_arguments(self, parser):
        parser.add_argument("--output", default="", help="Optional local JSON output path")
        parser.add_argument("--require-production", action="store_true", help="Fail if DEBUG is enabled")

    def handle(self, *args, **options):
        checks = assess()
        checks["production_mode"] = {"passed": not settings.DEBUG, "detail": "DEBUG disabled"}
        if settings.DEBUG and not options["require_production"]:
            checks["production_mode"]["passed"] = True
            checks["production_mode"]["detail"] = "Development-only evaluation; not production approval"
        try:
            connection = connections['default']
            executor = MigrationExecutor(connection)
            unapplied = executor.migration_plan(executor.loader.graph.leaf_nodes())
            checks["migrations"] = {"passed": not bool(unapplied), "detail": "No unapplied migrations" if not unapplied else "Apply outstanding migrations"}
        except Exception:
            checks["migrations"] = {"passed": False, "detail": "Migration inspection failed"}
        report = {"schema": 1, "phase": "5.3", "scope": "local_preflight_not_penetration_test", "passed": all(v['passed'] for v in checks.values()), "checks": checks}
        output = json.dumps(report, indent=2, sort_keys=True)
        if options['output']:
            from pathlib import Path
            path = Path(options['output'])
            if path.exists():
                raise CommandError("Refusing to overwrite an existing acceptance report")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(output + "\n", encoding="utf-8")
        self.stdout.write(output)
        if not report['passed']:
            raise CommandError("Release acceptance checks failed. Inspect the JSON checks above.")
