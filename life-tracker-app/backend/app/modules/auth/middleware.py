from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from app.modules.auth.sessions import COOKIE_NAME, password_required, token_valid

# Reachable without signing in.
PUBLIC_PATHS = {"/api/health", "/api/auth/status", "/api/auth/login", "/api/auth/logout"}


async def require_session(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Reject /api requests without a valid session cookie when an app password is set."""
    path = request.url.path
    if (
        password_required()
        and path.startswith("/api/")
        and path not in PUBLIC_PATHS
        and request.method != "OPTIONS"
        and not token_valid(request.cookies.get(COOKIE_NAME))
    ):
        return JSONResponse(status_code=401, content={"detail": "Sign in required."})
    return await call_next(request)
