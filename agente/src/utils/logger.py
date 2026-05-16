"""
Logging estruturado em JSON.
"""
import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def log(
    level: str,
    mensagem: str,
    processo_id: Optional[int] = None,
    etapa: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
):
    entrada = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level.upper(),
        "mensagem": mensagem,
    }
    if processo_id is not None:
        entrada["processo_id"] = processo_id
    if etapa is not None:
        entrada["etapa"] = etapa
    if extra:
        entrada.update(extra)
    print(json.dumps(entrada, ensure_ascii=False), flush=True)


def info(mensagem: str, **kwargs):
    log("INFO", mensagem, **kwargs)


def erro(mensagem: str, **kwargs):
    log("ERROR", mensagem, **kwargs)


def aviso(mensagem: str, **kwargs):
    log("WARN", mensagem, **kwargs)
