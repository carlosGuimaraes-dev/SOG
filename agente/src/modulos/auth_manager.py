"""
Gerenciador de autenticação Playwright com storage state e fallback interativo.
"""
import time
from pathlib import Path
from typing import Callable, Optional

from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext, TimeoutError as PlaywrightTimeout

from config import TIMEOUT_PADRAO
from utils.logger import info, erro, aviso


class ReautenticacaoNecessariaError(Exception):
    """Levantada quando a sessão expirou e requer login manual."""

    def __init__(self, sistema: str):
        self.sistema = sistema
        super().__init__(f"Reautenticação necessária no {sistema}")


class AuthManager:
    """
    Gerencia browser Playwright com:
    1. Carregamento de storage state (sessão reusável)
    2. Verificação de sessão ativa
    3. Fallback interativo (navegador visível) quando sessão expirou
    """

    def __init__(self, storage_path: Path, headless_default: bool = True):
        self.storage_path = storage_path
        self.headless_default = headless_default
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._playwright = None

    def iniciar(self, accept_downloads: bool = False):
        """Inicializa browser headless com storage state se disponível."""
        if self._playwright:
            return

        self._playwright = sync_playwright().start()
        self.browser = self._playwright.chromium.launch(headless=self.headless_default)

        context_kwargs = {
            "viewport": {"width": 1920, "height": 1080},
            "accept_downloads": accept_downloads,
        }
        if self.storage_path.exists():
            context_kwargs["storage_state"] = str(self.storage_path)

        self.context = self.browser.new_context(**context_kwargs)
        self.page = self.context.new_page()
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
        1. Inicia browser headless (com storage state se existir)
        2. Navega para url e verifica sessão
        3. Se válida → retorna True
        4. Se expirada → fallback interativo (navegador visível)
        5. Após login manual → salva storage state → reabre headless → retorna True
        """
        self.iniciar(accept_downloads=accept_downloads)

        self.page.goto(url, wait_until="networkidle")
        self.page.wait_for_timeout(2000)

        if verificar_sucesso_fn(self.page):
            return True

        # Sessão expirada — fallback interativo
        self._fallback_interativo(url, verificar_sucesso_fn, interativo_timeout_ms)
        return True

    def _fallback_interativo(
        self,
        url: str,
        verificar_sucesso_fn: Callable[[Page], bool],
        timeout_ms: int,
    ):
        """Abre navegador visível, aguarda login manual, salva storage state."""
        aviso("Sessão expirada. Abrindo navegador visível para reautenticação...")

        # Fecha headless atual
        self.fechar()

        # Abre visível
        self._playwright = sync_playwright().start()
        self.browser = self._playwright.chromium.launch(headless=False)
        self.context = self.browser.new_context(viewport={"width": 1920, "height": 1080})
        self.page = self.context.new_page()

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

        # Salva storage state
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.context.storage_state(path=str(self.storage_path))
        info(f"Storage state salvo em {self.storage_path}")

        # Fecha visível e reabre headless
        self.fechar()
        self.iniciar()

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
