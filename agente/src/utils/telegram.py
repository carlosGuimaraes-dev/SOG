"""
Notificações operacionais notify-only por Telegram.

As mensagens deste módulo aceitam somente dados operacionais agregados.
"""
from datetime import datetime
import os
from typing import Any, Callable, Dict, Iterable, Optional

import requests

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from utils.logger import erro, info


HttpPost = Callable[..., Any]


def _credenciais(
    token: Optional[str] = None,
    chat_id: Optional[str] = None,
) -> tuple[str, str]:
    return (
        token or os.getenv("TELEGRAM_BOT_TOKEN", TELEGRAM_BOT_TOKEN),
        chat_id or os.getenv("TELEGRAM_CHAT_ID", TELEGRAM_CHAT_ID),
    )


def enviar_mensagem(
    texto: str,
    *,
    http_post: HttpPost = requests.post,
    token: Optional[str] = None,
    chat_id: Optional[str] = None,
    timeout: int = 10,
) -> bool:
    """Envia mensagem notify-only via Bot API sem registrar webhooks/comandos."""
    token, chat_id = _credenciais(token, chat_id)
    if not token or not chat_id:
        info("Configuração Telegram incompleta — notificação não enviada.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": texto,
        "disable_web_page_preview": True,
    }

    try:
        response = http_post(url, json=payload, timeout=timeout)
    except requests.RequestException as exc:
        erro(f"Falha ao enviar Telegram: {exc}")
        return False

    status_code = getattr(response, "status_code", 200)
    if status_code >= 400:
        erro(f"Falha ao enviar Telegram: HTTP {status_code}")
        return False

    info("Notificação Telegram enviada com sucesso.")
    return True


def notificar_relogin_required(**kwargs: Any) -> bool:
    texto = "\n".join(
        [
            "[Custas TJDFT] Relogin necessário",
            "Sessão expirada. Agente pausado aguardando login manual.",
            "Acesse o dashboard para reautenticar e retomar a homologação.",
        ]
    )
    return enviar_mensagem(texto, **kwargs)


def notificar_erro_fatal(**kwargs: Any) -> bool:
    texto = "\n".join(
        [
            "[Custas TJDFT] Erro fatal",
            "Agente pausado por falha operacional.",
            "Acesse o dashboard e os logs do agente para diagnóstico.",
        ]
    )
    return enviar_mensagem(texto, **kwargs)


def notificar_resumo_lote(
    *,
    total: int,
    contagens_por_status: Dict[str, int],
    tempo_total: str,
    **kwargs: Any,
) -> bool:
    linhas_status = ", ".join(
        f"{status}: {total_status}"
        for status, total_status in sorted(contagens_por_status.items())
    ) or "sem itens"
    texto = "\n".join(
        [
            "[Custas TJDFT] Lote concluído",
            f"Total: {total}",
            f"Status: {linhas_status}",
            f"Tempo total: {tempo_total}",
            "Acesse o dashboard para revisar os detalhes operacionais.",
        ]
    )
    return enviar_mensagem(texto, **kwargs)


def notificar_ciclo_concluido(
    ciclo: Dict[str, Any],
    membros: Iterable[Dict[str, Any]],
    **kwargs: Any,
) -> bool:
    membros_lista = list(membros)
    contagens: Dict[str, int] = {}
    for membro in membros_lista:
        status = str(membro.get("status_atual") or membro.get("status_snapshot") or "desconhecido")
        contagens[status] = contagens.get(status, 0) + 1

    return notificar_resumo_lote(
        total=len(membros_lista),
        contagens_por_status=contagens,
        tempo_total=_tempo_total_ciclo(ciclo),
        **kwargs,
    )


def _tempo_total_ciclo(ciclo: Dict[str, Any]) -> str:
    inicio = _parse_data(ciclo.get("criado_em"))
    fim = _parse_data(ciclo.get("finalizado_em")) or datetime.now()
    if not inicio:
        return "indisponível"
    segundos = max(0, int((fim - inicio).total_seconds()))
    horas, resto = divmod(segundos, 3600)
    minutos, segundos = divmod(resto, 60)
    return f"{horas:02d}:{minutos:02d}:{segundos:02d}"


def _parse_data(valor: Any) -> Optional[datetime]:
    if not valor:
        return None
    texto = str(valor)
    for formato in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(texto[:19], formato)
        except ValueError:
            continue
    return None
