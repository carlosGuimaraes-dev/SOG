"""
Gerenciador de autenticacao Playwright baseado no profile persistente do SOG.
"""
import time
from pathlib import Path
from typing import Callable, Optional

from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

from config import TIMEOUT_PADRAO
from modulos.session_profile import SessionProfile
from utils.logger import aviso, info


class ReautenticacaoNecessariaError(Exception):
    """Levantada quando a sessao expirou e requer login manual."""

    def __init__(self, sistema: str):
        self.sistema = sistema
        super().__init__(f"Reautenticacao necessaria no {sistema}")


class AuthManager:
    """
    Gerencia browser Playwright com:
    1. Reutilizacao do mesmo profile persistente do navegador do SOG
    2. Verificacao de sessao ativa
    3. Fallback interativo quando a sessao expirou
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
        self._shared_session = False

    def iniciar(self, accept_downloads: bool = False):
        """Inicializa browser pelo profile persistente da sessao do SOG."""
        if self._playwright:
            return

        self._playwright = sync_playwright().start()
        browser, context = self.session_profile.connect_over_cdp(self._playwright.chromium)
        if browser and context:
            self._shared_session = True
            self.browser = browser
            self.context = context
            self.page = self.context.new_page()
        else:
            self._shared_session = False
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
        interativo_timeout_ms: int = 600_000,
    ) -> bool:
        """Verifica a sessao atual e cai no fluxo interativo se necessario."""
        self.iniciar(accept_downloads=accept_downloads)
        self.page.goto(url, wait_until="networkidle")
        self.page.wait_for_timeout(2000)

        if verificar_sucesso_fn(self.page):
            return True

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
        """Sempre abre o fluxo interativo visivel."""
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
        """Abre navegador visivel, aguarda login manual e salva snapshot compativel."""
        aviso("Sessao expirada. Abrindo navegador visivel para reautenticacao...")

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
        info("Navegador visivel aberto. Aguardando login manual...")

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

        self.session_profile.persist_storage_state(self.context)
        info(f"Storage state de compatibilidade salvo em {self.storage_path}")

        if manter_aberto_apos_login:
            info("Mantendo navegador visivel aberto para reutilizar a sessao autenticada.")
            return

        self.fechar()
        self.iniciar(accept_downloads=accept_downloads)

    def fechar(self):
        """Fecha context, browser e playwright de forma segura."""
        if self.page:
            try:
                if self._shared_session:
                    self.page.close()
            except Exception:
                pass
            self.page = None
        if self.context:
            try:
                if not self._shared_session:
                    self.context.close()
            except Exception:
                pass
            self.context = None
        if self.browser:
            try:
                if not self._shared_session:
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
        self._shared_session = False

    def __del__(self):
        self.fechar()
