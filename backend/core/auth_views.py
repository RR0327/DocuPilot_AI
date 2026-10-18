"""CSRF-protected, rate-limited, cookie-session endpoints."""
from django.conf import settings
from django.contrib.auth import logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.cache import never_cache
from .auth_security import enforce_session_idle, login_user
import json

def response(data, status=200):
    result = JsonResponse(data, status=status)
    result["Cache-Control"] = "no-store"
    return result

@require_GET
@ensure_csrf_cookie
@never_cache
def csrf(request):
    return response({"csrf_ready": True})

@require_POST
@csrf_protect
@never_cache
def session_login(request):
    if request.content_type != "application/json" or len(request.body) > 2048:
        return response({"detail": "Invalid login request."}, 400)
    try:
        fields = json.loads(request.body)
        username, password = fields.get("username", ""), fields.get("password", "")
    except (ValueError, AttributeError, TypeError):
        return response({"detail": "Invalid login request."}, 400)
    if not isinstance(username, str) or not isinstance(password, str) or not (1 <= len(username) <= 150) or not (1 <= len(password) <= 1024):
        return response({"detail": "Invalid login request."}, 400)
    user, reason = login_user(request, username, password)
    if reason == "rate_limited":
        result = response({"detail": "Too many attempts. Try again later."}, 429)
        result["Retry-After"] = str(settings.DOCUPILOT_LOGIN_WINDOW_SECONDS)
        return result
    if user is None:
        return response({"detail": "Invalid username or password."}, 401)
    return response({"username": user.get_username(), "authenticated": True})

@require_GET
@never_cache
def session_me(request):
    if not request.user.is_authenticated or enforce_session_idle(request):
        return response({"authenticated": False}, 401)
    return response({"username": request.user.get_username(), "authenticated": True})

@require_POST
@csrf_protect
@never_cache
def session_logout(request):
    logout(request)
    return response({"authenticated": False})
