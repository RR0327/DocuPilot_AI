"""Database-backed rate limiting and signed session security; no plaintext identifiers stored."""
import hashlib
import hmac
import time
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.utils.crypto import constant_time_compare
from .models import AuthenticationFailure


def client_ip(request):
    # Only the web server's socket address. Never trust forwarded headers supplied by browsers.
    return str(request.META.get("REMOTE_ADDR") or "unknown")[:100]

def digest(kind, value):
    data = f"docupilot-login-v1:{kind}:{value}".encode("utf-8")
    return hmac.new(settings.SECRET_KEY.encode("utf-8"), data, hashlib.sha256).hexdigest()

def buckets(request, username):
    return (digest("ip", client_ip(request)), digest("user-ip", f"{client_ip(request)}:{username.casefold()}"))

def blocked(keys):
    cutoff = timezone.now() - timedelta(seconds=settings.DOCUPILOT_LOGIN_WINDOW_SECONDS)
    return AuthenticationFailure.objects.filter(key_digest__in=keys, window_started__gte=cutoff, attempts__gte=settings.DOCUPILOT_LOGIN_FAILURE_LIMIT).exists()

def register_failure(keys):
    now = timezone.now()
    cutoff = now - timedelta(seconds=settings.DOCUPILOT_LOGIN_WINDOW_SECONDS)
    # SQLite serializes writers. Unique digest + atomic F update protects increments.
    for key in keys:
        with transaction.atomic():
            bucket, created = AuthenticationFailure.objects.get_or_create(key_digest=key, defaults={"window_started":now, "attempts":0})
            if not created and bucket.window_started < cutoff:
                AuthenticationFailure.objects.filter(pk=bucket.pk).update(window_started=now, attempts=0)
            AuthenticationFailure.objects.filter(pk=bucket.pk).update(attempts=F("attempts") + 1)

def reset_account_bucket(keys):
    # IP-wide bucket is intentionally not reset on success; hostile attempts must age out.
    AuthenticationFailure.objects.filter(key_digest=keys[1]).delete()

def login_user(request, username, password):
    keys = buckets(request, username)
    if blocked(keys):
        return None, "rate_limited"
    user = authenticate(request, username=username, password=password)
    if user is None or not user.is_active:
        register_failure(keys)
        return None, "invalid"
    reset_account_bucket(keys)
    login(request, user)  # rotates session key; prevents session fixation.
    request.session.set_expiry(settings.SESSION_COOKIE_AGE)
    request.session["docupilot_last_seen"] = int(time.time())
    return user, None

def enforce_session_idle(request):
    if not request.user.is_authenticated:
        return False
    now = int(time.time())
    previous = request.session.get("docupilot_last_seen")
    if previous is not None and (now - int(previous)) > settings.DOCUPILOT_SESSION_IDLE_SECONDS:
        logout(request)
        return True
    if previous is None or now - int(previous) >= 60:
        request.session["docupilot_last_seen"] = now
    return False
