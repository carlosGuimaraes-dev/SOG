"""
Gerenciador de autenticação Playwright baseado no profile persistente do SOG.
"""
import time
from pathlib import Path
from typing import Callable, Optional

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    TimeoutError as PlaywrightTimeout,
    sync_playwright,
)

from config import TIMEOUT_PADRAO
from modulos.session_profile import SessionProfile
from utils.logger import info, erro, aviso


class ReautenticacaoNecessariaError(Exception):
    """Levantada quando a sessão expirou e requer login manual."""

    def __init__(self, sistema: str):
        self.sistema = sistema
        super().__init__(f"Reautenticação necessária no {sistema}")


class AuthManager:
    """
    Gerencia browser Playwright com:
    1. Reutilização do mesmo profile persistente do navegador do SOG
    2. Verificação de sessão ativa
    3. Fallback interativo (navegador visível) quando sessão expirou
    """

    def __init__(self, storage_path: Path, headless_default: bool = True):
        self.storage_path = storage_path
        self.session_profile = SessionProfile(storage_path)
        self.profile_dir = self.session_profile.profile_dir
        self.headless_default = headless_default
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._playwright = None

    def iniciar(self, accept_downloads: bool = False):
        """Inicializa browser pelo profile persistente da sessão do SOG."""
        if self._playwright:
            return

        self._playwright = sync_playwright().start()
        self.context = self.session_profile.launch_persistent_context(
            self._playwright.chromium,
            headless=self.headless_default,
            accept_downloads=accept_downloads,
        )
        self.browser = self.context.browser
        self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
        self.page.set_default_timeout(TIMEOUT_PADRAO)

    def verificar_e_autenticar(
        self,
        url: str,
        verificar_sucesso_fn: Callable[[Page], bool],
        accept_downloads: bool = False,
        interativo_timeout_ms: int = 600_000,  # 10 minutos
    ) -> bool:
        """
        Fluxo completo:
        1. Inicia browser usando o profile persistente do SOG
        2. Navega para url e verifica sessão
        3. Se válida → retorna True
        4. Se expirada → fallback interativo (navegador visível)
        5. Após login manual → mantém a sessão original disponível
        """
        self.iniciar(accept_downloads=accept_downloads)

        self.page.goto(url, wait_until="networkidle")
        self.page.wait_for_timeout(2000)

        if verificar_sucesso_fn(self.page):
            return True

        # Sessão expirada — fallback interativo
        self._fallback_interativo(
            url,
            verificar_sucesso_fn,
            interativo_timeout_ms,
            accept_downloads=accept_downloads,
            manter_aberto_apos_login=True,
        )
        return True

    def forcar_reautenticacao_interativa(
        self,
        url: str,
        verificar_sucesso_fn: Callable[[Page], bool],
        accept_downloads: bool = False,
        interativo_timeout_ms: int = 600_000,
        manter_aberto_apos_login: bool = False,
    ) -> bool:
        """
        Sempre abre o fluxo interativo visível, mesmo que a sessão atual ainda pareça válida.
        """
        self.fechar()
        self._fallback_interativo(
            url,
            verificar_sucesso_fn,
            interativo_timeout_ms,
            accept_downloads=accept_downloads,
            manter_aberto_apos_login=manter_aberto_apos_login,
        )
        if manter_aberto_apos_login:
            return bool(self.page and verificar_sucesso_fn(self.page))
        self.fechar()
        self.iniciar(accept_downloads=accept_downloads)
        self.page.goto(url, wait_until="networkidle")
        self.page.wait_for_timeout(2000)
        return verificar_sucesso_fn(self.page)

    def _fallback_interativo(
        self,
        url: str,
        verificar_sucesso_fn: Callable[[Page], bool],
        timeout_ms: int,
        accept_downloads: bool = False,
        manter_aberto_apos_login: bool = False,
    ):
        """Abre navegador visível, aguarda login manual, salva storage state."""
        aviso("Sessão expirada. Abrindo navegador visível para reautenticação...")

        # Fecha headless atual
        self.fechar()

        self._playwright = sync_playwright().start()
        self.context = self.session_profile.launch_persistent_context(
            self._playwright.chromium,
            headless=False,
            accept_downloads=accept_downloads,
        )
        self.browser = self.context.browser
        self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
        self.page.set_default_timeout(TIMEOUT_PADRAO)

        self.page.goto(url, wait_until="networkidle")
        info("Navegador visível aberto. Aguardando login manual...")

        # Polling a cada 2s verificando se logou
        inicio = time.time()
        timeout_sec = timeout_ms / 1000
        logado = False

        while time.time() - inicio < timeout_sec:
            try:
                self.page.wait_for_timeout(2000)
                if verificar_sucesso_fn(self.page):
                    logado = True
                    break
            except Exception:
                pass

        if not logado:
            self.fechar()
            raise TimeoutError("Tempo esgotado aguardando login manual")

        # Mantém snapshot apenas como fallback de compatibilidade.
        self.session_profile.persist_storage_state(self.context)
        info(f"Storage state de compatibilidade salvo em {self.storage_path}")

        if manter_aberto_apos_login:
            info("Mantendo navegador visível aberto para reutilizar a sessão autenticada.")
            return

        # Fecha visível e reabre headless
        self.fechar()
        self.iniciar(accept_downloads=accept_downloads)

    def fechar(self):
        """Fecha context, browser e playwright de forma segura."""
        if self.context:
            try:
                self.context.close()
            except Exception:
                pass
            self.context = None
        if self.browser:
            try:
                self.browser.close()
            except Exception:
                pass
            self.browser = None
        if self._playwright:
            try:
                self._playwright.stop()
            except Exception:
                pass
            self._playwright = None
        self.page = None

    def __del__(self):
        self.fechar()
