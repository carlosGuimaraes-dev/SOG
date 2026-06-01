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


class BrowserIndisponivelError(RuntimeError):
    """Levantada quando o navegador Playwright não consegue iniciar."""


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

    def forcar_reautenticacao_interativa(
        self,
        url: str,
        verificar_sucesso_fn: Callable[[Page], bool],
        accept_downloads: bool = False,
        interativo_timeout_ms: int = 600_000,
    ) -> bool:
        """
        Sempre abre o fluxo interativo visível, mesmo que a sessão atual ainda pareça válida.
        """
        self.fechar()
        self._fallback_interativo(url, verificar_sucesso_fn, interativo_timeout_ms)
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
    ):
        """Abre navegador visível, aguarda login manual, salva storage state."""
        aviso("Sessão expirada. Abrindo navegador visível para reautenticação...")

        # Fecha headless atual
        self.fechar()

        # Abre visível
        try:
            self._playwright = sync_playwright().start()
            self.browser = self._playwright.chromium.launch(headless=False)
        except Exception as e:
            self.fechar()
            raise BrowserIndisponivelError(
                self._mensagem_browser_indisponivel(e, visivel=True)
            ) from e
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

    def _mensagem_browser_indisponivel(self, erro_original: Exception, visivel: bool) -> str:
        modo = "visível para login assistido" if visivel else "headless"
        detalhe = self._resumir_erro_playwright(erro_original)
        return (
            f"Não foi possível abrir o navegador {modo} do agente. "
            "O SOG tenta abrir o Chromium automaticamente para PJe e SISTJWEB quando a sessão precisa de login, "
            "mas o navegador fechou ao iniciar neste ambiente Docker. "
            "Verifique se o container tem suporte gráfico para janela visível ou execute o agente em um ambiente desktop "
            "com Playwright/Chromium habilitado. "
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
