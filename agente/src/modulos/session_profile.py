"""
Abstrai o perfil persistente usado pelo navegador do SOG.

O caminho principal do agente deve reutilizar o mesmo profile do navegador
controlado pelo operador; o storage_state fica apenas como snapshot de
compatibilidade.
"""
import os
from pathlib import Path


DEFAULT_CHROME_CDP_URL = "http://127.0.0.1:9222"


class SessionProfile:
    """Encapsula o diretório persistente e o snapshot opcional da sessão."""

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.profile_dir = storage_path.with_name(f"{storage_path.stem}_profile")

    def connect_over_cdp(self, chromium):
        """Conecta ao navegador de sessão do SOG quando ele já está aberto."""
        cdp_url = os.getenv("SOG_CHROME_CDP_URL", DEFAULT_CHROME_CDP_URL).strip()
        if not cdp_url:
            return None, None

        try:
            browser = chromium.connect_over_cdp(cdp_url)
        except Exception:
            return None, None

        if not browser.contexts:
            return None, None

        return browser, browser.contexts[0]

    def launch_persistent_context(self, chromium, *, headless: bool, accept_downloads: bool = False):
        """Abre o profile persistente que representa a sessão original do SOG."""
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        return chromium.launch_persistent_context(
            user_data_dir=str(self.profile_dir),
            headless=headless,
            viewport={"width": 1920, "height": 1080},
            accept_downloads=accept_downloads,
        )

    def persist_storage_state(self, context) -> None:
        """Mantém snapshot do storage_state apenas como fallback de compatibilidade."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        context.storage_state(path=str(self.storage_path))
