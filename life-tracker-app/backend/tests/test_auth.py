import time
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.modules.auth.sessions import COOKIE_NAME, create_token, login_attempts, token_valid

PASSWORD = "correct horse battery staple"

PROTECTED = [
    ("GET", "/api/movies"),
    ("GET", "/api/movies/tmdb/status"),
    ("GET", "/api/clothing/outfits"),
    ("GET", "/api/clothing/outfits/000000000000000000000000/photo"),
    ("GET", "/api/food/meals"),
    ("GET", "/api/food/foods"),
    ("GET", "/api/calendar?start=2025-01-01&end=2025-01-31"),
    ("POST", "/api/movies"),
    ("DELETE", "/api/movies/000000000000000000000000"),
]


@pytest.fixture
def password_on(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setattr(settings, "app_password", PASSWORD)
    monkeypatch.setattr(settings, "session_secret", "test-secret")
    # The test client talks plain http, where a Secure cookie would not be sent back.
    monkeypatch.setattr(settings, "session_cookie_secure", False)
    login_attempts.reset()
    yield
    login_attempts.reset()


def sign_in(client: TestClient) -> None:
    res = client.post("/api/auth/login", json={"password": PASSWORD})
    assert res.status_code == 204


# --- no password set (local development) ---


def test_no_password_means_no_login(client: TestClient) -> None:
    assert client.get("/api/auth/status").json() == {"required": False, "signed_in": True}
    assert client.get("/api/movies").status_code == 200


def test_login_is_a_no_op_without_password(client: TestClient) -> None:
    res = client.post("/api/auth/login", json={"password": "anything"})
    assert res.status_code == 204
    assert COOKIE_NAME not in res.cookies


# --- password set ---


@pytest.mark.usefixtures("password_on")
@pytest.mark.parametrize(("method", "path"), PROTECTED)
def test_data_routes_need_sign_in(client: TestClient, method: str, path: str) -> None:
    res = client.request(method, path)
    assert res.status_code == 401
    assert res.json() == {"detail": "Sign in required."}


@pytest.mark.usefixtures("password_on")
def test_public_routes_work_without_sign_in(client: TestClient) -> None:
    assert client.get("/api/health").status_code == 200
    assert client.get("/api/auth/status").json() == {"required": True, "signed_in": False}
    assert client.post("/api/auth/logout").status_code == 204


@pytest.mark.usefixtures("password_on")
def test_sign_in_opens_data_routes(client: TestClient) -> None:
    sign_in(client)
    assert client.get("/api/auth/status").json() == {"required": True, "signed_in": True}
    assert client.get("/api/movies").status_code == 200
    assert client.get("/api/clothing/outfits").status_code == 200


@pytest.mark.usefixtures("password_on")
def test_wrong_password_is_rejected_without_cookie(client: TestClient) -> None:
    res = client.post("/api/auth/login", json={"password": "nope"})
    assert res.status_code == 401
    assert res.json() == {"detail": "Wrong password."}
    assert COOKIE_NAME not in res.cookies
    assert client.get("/api/movies").status_code == 401


@pytest.mark.usefixtures("password_on")
def test_too_many_wrong_passwords_are_blocked(client: TestClient) -> None:
    for _ in range(10):
        assert client.post("/api/auth/login", json={"password": "nope"}).status_code == 401
    res = client.post("/api/auth/login", json={"password": PASSWORD})
    assert res.status_code == 429
    assert COOKIE_NAME not in res.cookies


@pytest.mark.usefixtures("password_on")
def test_logout_signs_out(client: TestClient) -> None:
    sign_in(client)
    res = client.post("/api/auth/logout")
    assert res.status_code == 204
    assert client.get("/api/movies").status_code == 401


@pytest.mark.usefixtures("password_on")
def test_cookie_attributes(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "session_cookie_secure", True)
    res = client.post("/api/auth/login", json={"password": PASSWORD})
    header = res.headers["set-cookie"].lower()
    assert f"{COOKIE_NAME}=" in header
    for attribute in ("httponly", "secure", "samesite=lax", "path=/", "max-age=7776000"):
        assert attribute in header


@pytest.mark.usefixtures("password_on")
def test_tampered_cookie_is_rejected(client: TestClient) -> None:
    token = create_token()
    version, expires, signature = token.split(".")
    forged = f"{version}.{int(expires) + 86400}.{signature}"
    client.cookies.set(COOKIE_NAME, forged)
    assert client.get("/api/movies").status_code == 401
    client.cookies.set(COOKIE_NAME, "garbage")
    assert client.get("/api/movies").status_code == 401


@pytest.mark.usefixtures("password_on")
def test_expired_token_is_rejected() -> None:
    old = create_token(now=time.time() - 91 * 86400)
    assert not token_valid(old)
    assert token_valid(create_token())


@pytest.mark.usefixtures("password_on")
def test_changing_password_signs_everyone_out(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    sign_in(client)
    monkeypatch.setattr(settings, "app_password", "a new password")
    assert client.get("/api/movies").status_code == 401
