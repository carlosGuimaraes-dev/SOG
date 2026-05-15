"""
API FastAPI para dashboard de aprovação de custas TJDFT.
"""
import time
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from rotas import auth, processos, aprovacao, historico

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("custas_api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("API iniciada")
    yield
    logger.info("API encerrada")


app = FastAPI(
    title="Custas TJDFT API",
    version="1.1.0",
    description="API de gerenciamento de custas processuais",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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


# Tratamento global de exceções
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error("Erro não tratado em %s: %s", request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Erro interno do servidor"},
    )


# Health check (público, sem auth)
@app.get("/health", tags=["health"])
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
