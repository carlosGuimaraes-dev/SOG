"""
Classe base para clientes Playwright (PJE e SISTJWEB).

Extrai a lógica comum de inicialização, teardown, verificação de sessão
e reconexão, evitando duplicação entre PjeClient e SistjClient.
"""
from typing import Optional

from playwright.sync_api import Page, Browser, TimeoutError as PlaywrightTimeout

from modulos.auth_manager import AuthManager
from utils.logger import info, erro


class PlaywrightClient:
    """Cliente base para automação com Playwright."""

    def __init__(self):
        self._auth: Optional[AuthManager] = None

    @property
    def page(self) -> Optional[Page]:
        return self._auth.page if self._auth else None

    @property
    def browser(self) -> Optional[Browser]:
        return self._auth.browser if self._auth else None

    def fechar(self):
        """Fecha o navegador e libera recursos do Playwright."""
        if self._auth:
            self._auth.fechar()

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
