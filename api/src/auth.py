"""
Autenticação JWT para a API do dashboard.
"""
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from sog_shared import db

# ---------------------------------------------------------------------------
# Configurações JWT
# ---------------------------------------------------------------------------
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY or len(JWT_SECRET_KEY) < 32:
    raise RuntimeError(
        "JWT_SECRET_KEY deve estar configurada no ambiente com pelo menos 32 caracteres."
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7
JWT_ISSUER = os.getenv("JWT_ISSUER", "sog-api")
JWT_AUDIENCE = "custas-dashboard"

security = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Token creation / decoding
# ---------------------------------------------------------------------------
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "iat": now,
        "exp": expire,
        "sub": data.get("sub"),
        "type": "access",
    })
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    jti = str(uuid.uuid4())
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "iat": now,
        "exp": expire,
        "sub": data.get("sub"),
        "type": "refresh",
        "jti": jti,
    })
    token = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)

    # Persiste no banco para permitir revogação e rotação
    with db.get_conn() as conn:
        conn.execute(
            "INSERT INTO refresh_tokens (token_jti, user_id, expires_at) VALUES (?, ?, ?)",
            (jti, data.get("sub"), expire.isoformat()),
        )
        conn.commit()

    return token


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[ALGORITHM],
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER,
        )
        return payload
    except JWTError:
        return None


# ---------------------------------------------------------------------------
# Dependency — current user
# ---------------------------------------------------------------------------
def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    # Prioriza cookie httpOnly; fallback para Authorization header
    token = request.cookies.get("access_token")
    if not token and credentials:
        token = credentials.credentials

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação não fornecido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username: str = payload.get("sub")
    token_type: str = payload.get("type")
    if username is None or token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return username


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------
def authenticate_user(username: str, password: str) -> bool:
    """Verifica credenciais do dashboard salvas no SQLite."""
    credenciais = db.obter_credenciais_dashboard()
    if not credenciais:
        return False
    if username != credenciais["usuario"]:
        return False
    return password == credenciais["senha"]


# ---------------------------------------------------------------------------
# Refresh-token rotation helpers
# ---------------------------------------------------------------------------
def refresh_token_eh_valido(jti: str) -> bool:
    with db.get_conn() as conn:
        row = conn.execute(
            "SELECT revoked_at, expires_at FROM refresh_tokens WHERE token_jti = ?",
            (jti,),
        ).fetchone()
        if not row:
            return False
        if row["revoked_at"] is not None:
            return False
        # expires_at está armazenado como ISO string
        try:
            expires = datetime.fromisoformat(row["expires_at"])
        except (ValueError, TypeError):
            return False
        if datetime.now(timezone.utc) > expires:
            return False
        return True


def revogar_refresh_token(jti: str) -> None:
    with db.get_conn() as conn:
        conn.execute(
            "UPDATE refresh_tokens SET revoked_at = CURRENT_TIMESTAMP WHERE token_jti = ?",
            (jti,),
        )
        conn.commit()
