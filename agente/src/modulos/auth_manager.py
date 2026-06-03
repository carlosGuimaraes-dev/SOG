"""
Gerenciador de autenticação Playwright com storage state.
"""
from pathlib import Path
from typing import Callable, Optional

from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext

from config import TIMEOUT_PADRAO


class ReautenticacaoNecessariaError(Exception):
    """Levantada quando a sessão expirou e requer login manual."""

    def __init__(self, sistema: str):
        self.sistema = sistema
        super().__init__(f"Reautenticação necessária no {sistema}")


class BrowserIndisponivelError(RuntimeError):
    """Levantada quando o navegador Playwright não consegue iniciar."""


class AuthManager:
    """
    Gerencia browser Playwright com:
    1. Carregamento de storage state (sessão reusável)
    2. Verificação de sessão ativa
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

        try:
            self._playwright = sync_playwright().start()
            self.browser = self._playwright.chromium.launch(headless=self.headless_default)
        except Exception as e:
            self.fechar()
            raise BrowserIndisponivelError(
                self._mensagem_browser_indisponivel(e, visivel=not self.headless_default)
            ) from e

        context_kwargs = {
            "viewport": {"width": 1920, "height": 1080},
            "accept_downloads": accept_downloads,
        }
        if self.storage_path.exists():
            context_kwargs["storage_state"] = str(self.storage_path)

        self.context = self.browser.new_context(**context_kwargs)
        self.page = self.context.new_page()
        self.page.set_default_timeout(TIMEOUT_PADRAO)

    def verificar_sessao(
        self,
        url: str,
        verificar_sucesso_fn: Callable[[Page], bool],
        accept_downloads: bool = False,
    ) -> bool:
        """Verifica storage_state existente sem abrir navegador de login."""
        self.iniciar(accept_downloads=accept_downloads)
        self.page.goto(url, wait_until="networkidle")
        self.page.wait_for_timeout(2000)
        return verificar_sucesso_fn(self.page)

    def _mensagem_browser_indisponivel(self, erro_original: Exception, visivel: bool) -> str:
        modo = "visível para login assistido" if visivel else "headless"
        detalhe = self._resumir_erro_playwright(erro_original)
        return (
            f"Não foi possível abrir o navegador {modo} do agente. "
            "Abra o Chrome pelo botão Abrir Chrome para login no SOG Desktop, conclua PJe e SISTJWEB, "
            "e retome o agente quando as duas sessões estiverem autenticadas. "
            f"Detalhe técnico resumido: {detalhe}"
        )

    def _resumir_erro_playwright(self, erro_original: Exception) -> str:
        texto = str(erro_original).replace("\n", " ")
        marcadores = [
            "Target page, context or browser has been closed",
            "Host system is missing dependencies",
            "Connection reset by peer",
            "No such file or directory",
        ]
        for marcador in marcadores:
            if marcador in texto:
                return marcador
        return texto[:240] + ("..." if len(texto) > 240 else "")

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
