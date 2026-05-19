"""
Executor de tarefas sob demanda do agente.
Mapeia tipos de tarefa para funções que usam PjeClient/SistjClient.
"""
from typing import Dict, Any, Callable

from utils.logger import info, erro, aviso

# Registry de handlers
_HANDLERS: Dict[str, Callable] = {}


def registrar(tipo: str):
    """Decorador para registrar handler de tarefa."""
    def wrapper(fn: Callable):
        _HANDLERS[tipo] = fn
        return fn
    return wrapper


def executar_tarefa(tarefa: Dict[str, Any], pje, sistj) -> Dict[str, Any]:
    """Executa uma tarefa e retorna o resultado."""
    tipo = tarefa["tipo"]
    payload = tarefa.get("payload") or {}

    handler = _HANDLERS.get(tipo)
    if not handler:
        raise ValueError(f"Tipo de tarefa desconhecido: {tipo}")

    return handler(payload, pje, sistj)


def tipos_suportados() -> list:
    return list(_HANDLERS.keys())


# ── Handlers (serão implementados nas waves seguintes) ──────────────────

@registrar("verificar_sessao_pje")
def _verificar_sessao_pje(payload, pje, sistj):
    """Handler placeholder — implementado na Wave 2."""
    try:
        logado = pje._esta_logado(pje.page)
        return {"logado": logado, "url_atual": pje.page.url}
    except Exception:
        return {"logado": False, "url_atual": None}
