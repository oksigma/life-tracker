"""Signed session tokens and the login-attempt limiter for the single app password (spec 0006).

A token is "v1.<expiry unix seconds>.<hmac>". Nothing is stored server side.
The signing key is derived from SESSION_SECRET and APP_PASSWORD, so changing the password
invalidates every existing session.
"""

import hashlib
import hmac
import time
from collections import deque

from app.core.config import settings

COOKIE_NAME = "lifetracker_session"
VERSION = "v1"


def password_required() -> bool:
    return bool(settings.app_password)


def _key() -> bytes:
    material = f"{settings.session_secret}\0{settings.app_password}".encode()
    return hashlib.sha256(material).digest()


def _sign(payload: str) -> str:
    return hmac.new(_key(), payload.encode(), hashlib.sha256).hexdigest()


def create_token(now: float | None = None) -> str:
    expires = int((now if now is not None else time.time()) + settings.session_days * 86400)
    payload = f"{VERSION}.{expires}"
    return f"{payload}.{_sign(payload)}"


def token_valid(token: str | None, now: float | None = None) -> bool:
    if not token:
        return False
    parts = token.split(".")
    if len(parts) != 3 or parts[0] != VERSION or not parts[1].isdigit():
        return False
    payload = f"{parts[0]}.{parts[1]}"
    if not hmac.compare_digest(parts[2], _sign(payload)):
        return False
    return int(parts[1]) > (now if now is not None else time.time())


def password_matches(candidate: str) -> bool:
    # Compare digests so the comparison is constant time regardless of length.
    expected = hashlib.sha256(settings.app_password.encode()).digest()
    given = hashlib.sha256(candidate.encode()).digest()
    return hmac.compare_digest(expected, given)


class AttemptLimiter:
    """Allows at most `max_failures` wrong passwords per `window_seconds` (per process)."""

    def __init__(self, max_failures: int = 10, window_seconds: float = 15 * 60) -> None:
        self.max_failures = max_failures
        self.window_seconds = window_seconds
        self._failures: deque[float] = deque()

    def _prune(self, now: float) -> None:
        while self._failures and now - self._failures[0] >= self.window_seconds:
            self._failures.popleft()

    def blocked(self, now: float | None = None) -> bool:
        now = now if now is not None else time.monotonic()
        self._prune(now)
        return len(self._failures) >= self.max_failures

    def record_failure(self, now: float | None = None) -> None:
        self._failures.append(now if now is not None else time.monotonic())

    def reset(self) -> None:
        self._failures.clear()


login_attempts = AttemptLimiter()
