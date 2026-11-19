from typing import Annotated

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, StringConstraints

from app.core.config import settings
from app.modules.auth.sessions import (
    COOKIE_NAME,
    create_token,
    login_attempts,
    password_matches,
    password_required,
    token_valid,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class AuthStatus(BaseModel):
    required: bool
    signed_in: bool


class LoginRequest(BaseModel):
    password: Annotated[str, StringConstraints(max_length=500)]


@router.get("/status")
async def auth_status(request: Request) -> AuthStatus:
    required = password_required()
    signed_in = not required or token_valid(request.cookies.get(COOKIE_NAME))
    return AuthStatus(required=required, signed_in=signed_in)


@router.post("/login", status_code=status.HTTP_204_NO_CONTENT)
async def login(body: LoginRequest, response: Response) -> None:
    if not password_required():
        return
    if login_attempts.blocked():
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, "Too many attempts, try again later."
        )
    if not password_matches(body.password):
        login_attempts.record_failure()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong password.")
    response.set_cookie(
        COOKIE_NAME,
        create_token(),
        max_age=settings.session_days * 86400,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> None:
    response.delete_cookie(
        COOKIE_NAME, path="/", httponly=True, secure=settings.session_cookie_secure, samesite="lax"
    )
