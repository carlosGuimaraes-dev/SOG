"""
API FastAPI para dashboard de aprovação de custas TJDFT.
"""
import os
import time
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from limiter import limiter
from schemas import HealthResponse

from sog_shared import db
from sog_shared.config import init_config
from rotas import auth, processos, aprovacao, historico, agente, tarefas, pje, sistjweb, acoes, dashboard

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("custas_api")



@asynccontextmanager
async def lifespan(app: FastAPI):
    init_config()
    db.init_db()
    dashboard_usuario = os.getenv("DASHBOARD_USUARIO", "").strip()
    dashboard_senha = os.getenv("DASHBOARD_SENHA", "")
    if dashboard_usuario and dashboard_senha:
        db.salvar_credenciais_dashboard(dashboard_usuario, dashboard_senha)
    logger.info("API iniciada")
    yield
    logger.info("API encerrada")


app = FastAPI(
    title="Custas TJDFT API",
    version="1.1.0",
    description="API de gerenciamento de custas processuais",
    lifespan=lifespan,
    root_path="/api/v1",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
_frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[_frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware de logging e tempo de resposta
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = (time.time() - start) * 1000
    logger.info(
        "%s %s — %d — %.1fms",
        request.method,
        request.url.path,
        response.status_code,
        duration,
    )
    return response


# Tratamento de exceções — handlers específicos primeiro
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning("Erro de validação em %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Dados de entrada inválidos"},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning("HTTPException em %s: %d — %s", request.url.path, exc.status_code, exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


# Catch-all genérico — NUNCA expõe str(exc) ao cliente
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error("Erro não tratado em %s: %s", request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Erro interno do servidor"},
    )


# Health check (público, sem auth)
@app.get("/health", response_model=HealthResponse, tags=["health"])
def health():
    db_ok = True
    try:
        with db.get_conn() as conn:
            conn.execute("SELECT 1").fetchone()
    except Exception:
        db_ok = False
    return {
        "status": "ok" if db_ok else "degraded",
        "version": "1.1.0",
        "database": "ok" if db_ok else "error",
    }


# Registro de rotas
app.include_router(auth.router)
app.include_router(processos.router)
app.include_router(aprovacao.router)
app.include_router(historico.router)
app.include_router(agente.router)
app.include_router(tarefas.router)
app.include_router(pje.router)
app.include_router(sistjweb.router)
app.include_router(acoes.router)
app.include_router(dashboard.router)
