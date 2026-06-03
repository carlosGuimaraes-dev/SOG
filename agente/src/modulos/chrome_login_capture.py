"""
Captura storage_state a partir do Google Chrome aberto pelo usuário com CDP local.
"""
import os
from pathlib import Path
from typing import Callable

from playwright.sync_api import Page, sync_playwright


CDP_URL_DEFAULT = "http://127.0.0.1:9222"


def capturar_sessoes_chrome(
    verificar_pje_fn: Callable[[Page], bool],
    verificar_sistj_fn: Callable[[Page], bool],
    storage_pje: Path,
    storage_sistj: Path,
    cdp_url: str | None = None,
) -> dict:
    cdp_url = cdp_url or os.getenv("SOG_CHROME_CDP_URL", CDP_URL_DEFAULT)

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.connect_over_cdp(cdp_url)
            pages = [page for context in browser.contexts for page in context.pages]

            pje_page = _buscar_pagina(pages, "pje")
            sistj_page = _buscar_pagina(pages, "sistjweb")
            missing = []
            if not pje_page:
                missing.append("pje")
            if not sistj_page:
                missing.append("sistjweb")
            if missing:
                return _aguardando("abas_ausentes", missing=missing)

            pending = []
            if not verificar_pje_fn(pje_page):
                pending.append("pje")
            if not verificar_sistj_fn(sistj_page):
                pending.append("sistjweb")
            if pending:
                return _aguardando("login_pendente", pending=pending)

            storage_pje.parent.mkdir(parents=True, exist_ok=True)
            storage_sistj.parent.mkdir(parents=True, exist_ok=True)
            pje_page.context.storage_state(path=str(storage_pje))
            sistj_page.context.storage_state(path=str(storage_sistj))
            return {
                "ok": True,
                "pje_url": pje_page.url,
                "sistj_url": sistj_page.url,
            }
    except Exception as exc:
        return _aguardando("chrome_indisponivel", error=str(exc))


def _buscar_pagina(pages: list[Page], sistema: str):
    for page in pages:
        url = getattr(page, "url", "").lower()
        if sistema == "pje" and (
            "pje.tjdft.jus.br" in url or "sso.cloud.pje.jus.br" in url
        ):
            return page
        if sistema == "sistjweb" and (
            "sistj.tjdft.jus.br" in url
            or "sso.tjdft.jus.br" in url
            or "login.microsoftonline.com" in url
        ):
            return page
    return None


def _aguardando(reason: str, **extra) -> dict:
    return {
        "ok": False,
        "reason": reason,
        **extra,
    }
