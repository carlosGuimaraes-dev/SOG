"""
Autenticação JWT para a API do dashboard.
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "agente" / "src"))

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext

from config import DASHBOARD_USUARIO, DASHBOARD_SENHA_HASH

# Configurações JWT
SECRET_KEY = DASHBOARD_SENHA_HASH or "dev-secret-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)


def verify_password(plain: str, hashed: str) -> bool:
    if not hashed or len(hashed) < 10:
        return False
    try:
        return pwd_context.verify(plain, hashed)
    except ValueError:
        return False


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação não fornecido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(credentials.credentials)
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


def _hash_valido(hashed: str) -> bool:
    """Verifica se a string parece um hash bcrypt válido."""
    return bool(hashed and hashed.startswith(("$2a$", "$2b$", "$2x$", "$2y$")) and len(hashed) >= 59)


def authenticate_user(username: str, password: str) -> bool:
    """Verifica credenciais contra .env. Em dev, aceita qualquer senha se hash ausente ou inválido."""
    if username != DASHBOARD_USUARIO:
        return False
    if not _hash_valido(DASHBOARD_SENHA_HASH):
        return True  # modo desenvolvimento — hash ausente/inválido
    return verify_password(password, DASHBOARD_SENHA_HASH)
