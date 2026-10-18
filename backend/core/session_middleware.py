from .auth_security import enforce_session_idle

class SessionIdleMiddleware:
    """Enforce idle expiry for all authenticated requests, including private PDF streams."""
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        if request.path.startswith("/api/") and hasattr(request, "user") and request.user.is_authenticated:
            enforce_session_idle(request)
        return self.get_response(request)
