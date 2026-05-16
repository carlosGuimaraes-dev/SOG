"""
Classe base para clientes Playwright (PJE e SISTJWEB).

Extrai a lógica comum de inicialização, teardown, verificação de sessão
e reconexão, evitando duplicação entre PjeClient e SistjClient.
"""
from typing import Optional
from playwright.sync_api import sync_playwright, Page, Browser, TimeoutError as PlaywrightTimeout

from config import HEADLESS, TIMEOUT_PADRAO
from utils.logger import info, erro


class PlaywrightClient:
    """Cliente base para automação com Playwright."""

    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self._playwright = None

    def iniciar(self, accept_downloads: bool = False):
        """Inicializa navegador, contexto e página com viewport padrão."""
        self._playwright = sync_playwright().start()
        self.browser = self._playwright.chromium.launch(headless=HEADLESS)
        context = self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            accept_downloads=accept_downloads,
        )
        self.page = context.new_page()
        self.page.set_default_timeout(TIMEOUT_PADRAO)

    def fechar(self):
        """Fecha o navegador e libera recursos do Playwright."""
        if self.browser:
            self.browser.close()
        if self._playwright:
            self._playwright.stop()

    def verificar_sessao(self) -> bool:
        """Retorna True se a sessão estiver expirada ou inválida."""
        if not self.page:
            return True
        from modulos.retry import is_session_expired
        return is_session_expired(self.page)

    def reconectar(self) -> bool:
        """Refaz login. Retorna True em caso de sucesso."""
        try:
            nome = self.__class__.__name__
            info(f"Reconectando ao {nome}...")
            if self.login():
                info(f"Reconexão {nome} bem-sucedida.")
                return True
            erro(f"Reconexão {nome} falhou: login retornou False.")
            return False
        except Exception as e:
            erro(f"Falha na reconexão {self.__class__.__name__}: {e}")
            return False

    def login(self) -> bool:
        """Deve ser implementado pela subclasse."""
        raise NotImplementedError("Subclasses devem implementar login()")
