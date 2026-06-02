"""
Rotas de autenticação JWT via httpOnly cookies.
"""
import os

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi import Request

from limiter import limiter
from auth import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    dashboard_auth_disabled,
    decode_token,
    get_current_user,
    refresh_token_eh_valido,
    revogar_refresh_token,
)
from schemas import LoginResponse, TokenRefreshResponse, LogoutResponse, MeResponse

router = APIRouter(prefix="/auth", tags=["auth"])

_IS_DEV = os.getenv("ENV", "production") == "development"
_COOKIE_SECURE = not _IS_DEV
_COOKIE_SAMESITE = "Lax" if _IS_DEV else "Strict"
_ACCESS_MAX_AGE = 3600
_REFRESH_MAX_AGE = 604800


class LoginRequest(BaseModel):
    username: str
    password: str


def _set_auth_cookies(response: Response, access: str, refresh: str) -> None:
    response.set_cookie(
        key="access_token",
        value=access,
        max_age=_ACCESS_MAX_AGE,
        httponly=True,
        secure=_COOKIE_SECURE,
        samesite=_COOKIE_SAMESITE,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh,
        max_age=_REFRESH_MAX_AGE,
        httponly=True,
        secure=_COOKIE_SECURE,
        samesite=_COOKIE_SAMESITE,
        path="/",
    )


def _clear_auth_cookies(response: Response) -> None:
    response.set_cookie(
        key="access_token",
        value="",
        max_age=0,
        httponly=True,
        secure=_COOKIE_SECURE,
        samesite=_COOKIE_SAMESITE,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value="",
        max_age=0,
        httponly=True,
        secure=_COOKIE_SECURE,
        samesite=_COOKIE_SAMESITE,
        path="/",
    )


def _json_response_with_cleared_cookies(
    status_code: int, content: dict
) -> JSONResponse:
    """Retorna JSONResponse com cookies de auth limpos (para erros 401)."""
    response = JSONResponse(status_code=status_code, content=content)
    response.set_cookie(
        key="access_token",
        value="",
        max_age=0,
        httponly=True,
        secure=_COOKIE_SECURE,
        samesite=_COOKIE_SAMESITE,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value="",
        max_age=0,
        httponly=True,
        secure=_COOKIE_SECURE,
        samesite=_COOKIE_SAMESITE,
        path="/",
    )
    return response


@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
def login(req: LoginRequest, response: Response, request: Request):
    if dashboard_auth_disabled():
        return {"message": "Login dispensado no modo desktop local"}

    if not authenticate_user(req.username, req.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
        )
    access = create_access_token({"sub": req.username})
    refresh = create_refresh_token({"sub": req.username})
    _set_auth_cookies(response, access, refresh)
    return {"message": "Login realizado"}


@router.post("/refresh", response_model=TokenRefreshResponse)
def refresh(request: Request, response: Response):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        return _json_response_with_cleared_cookies(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Refresh token não fornecido"},
        )

    payload = decode_token(refresh_token)
    if payload is None or payload.get("type") != "refresh":
        return _json_response_with_cleared_cookies(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Refresh token inválido ou expirado"},
        )

    jti = payload.get("jti")
    username = payload.get("sub")
    if not jti or not username:
        return _json_response_with_cleared_cookies(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Refresh token inválido"},
        )

    if not refresh_token_eh_valido(jti):
        return _json_response_with_cleared_cookies(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Refresh token revogado ou expirado"},
        )

    # Rotação: revoga o token usado e emite um par NOVO
    revogar_refresh_token(jti)
    access = create_access_token({"sub": username})
    refresh = create_refresh_token({"sub": username})
    _set_auth_cookies(response, access, refresh)
    return {"message": "Token atualizado"}


@router.get("/me", response_model=MeResponse)
def me(username: str = Depends(get_current_user)):
    return {"username": username, "auth_required": not dashboard_auth_disabled()}


@router.post("/logout", response_model=LogoutResponse)
def logout(request: Request, response: Response):
    if dashboard_auth_disabled():
        _clear_auth_cookies(response)
        return {"message": "Logout dispensado no modo desktop local"}

    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        payload = decode_token(refresh_token)
        if payload and payload.get("type") == "refresh":
            jti = payload.get("jti")
            if jti:
                revogar_refresh_token(jti)
    _clear_auth_cookies(response)
    return {"message": "Logout realizado"}
