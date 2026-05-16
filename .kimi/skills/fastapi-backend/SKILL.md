---
name: fastapi-backend
description: Desenvolvimento FastAPI para APIs REST. Estrutura em camadas, routers com tags, schemas Pydantic v2, autenticação JWT com httpOnly cookies, dependency injection, tratamento de erros, logging estruturado e documentação OpenAPI automática.
---

# FastAPI Backend

## Resumo

Construção de APIs REST robustas com FastAPI, organizadas em camadas, com autenticação segura via JWT em cookies httpOnly e documentação OpenAPI automática.

## Quando usar

- APIs REST para dashboards ou backends de automação
- Projetos que precisam de validação automática de dados
- Sistemas com autenticação por sessão (JWT em cookies)
- Quando documentação interativa (Swagger) é desejável

## Padrões principais

### 1. Estrutura de projeto em camadas

```
api/
├── src/
│   ├── main.py
│   ├── config.py
│   ├── dependencies.py
│   ├── routers/
│   │   ├── __init__.py
│   │   └── processos.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── processo.py
│   ├── services/
│   │   └── processo_service.py
│   └── db.py
```

### 2. Routers com tags

```python
from fastapi import APIRouter

router = APIRouter(prefix="/processos", tags=["Processos"])

@router.get("/{numero}")
async def get_processo(numero: str):
    ...
```

### 3. Schemas Pydantic v2

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class ProcessoBase(BaseModel):
    numero: str = Field(..., pattern=r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}")
    valor_custas: float = Field(..., ge=0)

class ProcessoCreate(ProcessoBase):
    pass

class ProcessoOut(ProcessoBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
```

### 4. Autenticação JWT com httpOnly cookies

```python
from fastapi import Depends, HTTPException, Response, Request
from fastapi.security import HTTPBearer
import jwt
from datetime import datetime, timedelta

SECRET = "your-secret"
ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: timedelta = timedelta(hours=24)) -> str:
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + expires_delta
    return jwt.encode(to_encode, SECRET, algorithm=ALGORITHM)

def set_auth_cookie(response: Response, token: str):
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=86400,
    )

async def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Não autenticado")
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
```

### 5. Dependency injection

```python
from fastapi import Depends
from sqlalchemy.orm import Session
from .db import get_db

async def get_processo_service(db: Session = Depends(get_db)):
    return ProcessoService(db)

@router.get("/{numero}")
async def get_processo(
    numero: str,
    service: ProcessoService = Depends(get_processo_service),
    user: str = Depends(get_current_user),
):
    return service.get(numero)
```

### 6. Tratamento de erros

```python
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": "Dados inválidos", "errors": exc.errors()},
    )
```

### 7. Logging estruturado

```python
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
        })

handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger = logging.getLogger("api")
logger.addHandler(handler)
logger.setLevel(logging.INFO)
```

## Anti-patterns

- Retornar senhas ou tokens no corpo da resposta JSON
- Usar `dict` em vez de schemas Pydantic para validação
- Fazer queries SQL diretamente nos routers
- Ignorar exceções sem logging adequado
- Configurar CORS com `allow_origins=["*"]` em produção
- Usar JWT sem expiração
