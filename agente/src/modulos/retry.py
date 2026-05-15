"""
Módulo de retry robusto com detecção de sessão expirada e reconexão automática.

Uso:
    @retry_on_exception(exceptions=(PlaywrightTimeout, Exception), max_retries=3, backoff=2)
    def metodo_critico(self, ...):
        ...
"""
import time
import re
from functools import wraps
from typing import Tuple, Type, Union

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout

from utils.logger import info, erro, aviso


# Padrões de texto que indicam sessão expirada em diversos sistemas judiciais
_SESSAO_EXPIRADA_PADROES = [
    r"sua sess[ãa]o expirou",
    r"sess[ãa]o expirada",
    r"sess[ãa]o encerrada",
    r"efetue o login",
    r"fa[çc]a login",
    r"autentica[çc][ãa]o necess[áa]ria",
    r"usu[áa]rio n[ãa]o autenticado",
    r"login obrigat[óo]rio",
    r"tempo de sess[ãa]o esgotado",
    r"sess[ãa]o inv[áa]lida",
    r"sua sess[ãa]o expira em",
    r"session expired",
    r"please log in",
    r"unauthorized",
    r"n[ãa]o autorizado",
    r"acesso negado",
]

_SESSAO_EXPIRADA_REGEX = re.compile("|".join(_SESSAO_EXPIRADA_PADROES), re.IGNORECASE)

# Erros de credenciais que NÃO devem ser retried
_CREDENTIAL_ERRORS = [
    "401",
    "403",
    "unauthorized",
    "forbidden",
    "acesso negado",
    "não autorizado",
    "credenciais inválidas",
    "senha incorreta",
    "usuário inválido",
    "authentication failed",
]


def is_session_expired(page: Page) -> bool:
    """
    Detecta se a sessão atual expirou analisando URL, título e conteúdo da página.

    Args:
        page: Instância do Playwright Page.

    Returns:
        True se indícios de sessão expirada forem encontrados.
    """
    if not page:
        return True

    try:
        url = page.url.lower()
        # Redirect para páginas de login ou autenticação
        if any(fragment in url for fragment in ["login", "autentica", "sessao", "session", "logon"]):
            # Confirma que não é apenas uma URL com 'login' no meio de um fluxo normal
            # (alguns sistemas podem ter 'login' na URL mesmo logado, então cruzamos com conteúdo)
            pass

        # Tenta obter título e conteúdo de forma segura
        title = ""
        content = ""
        try:
            title = page.title().lower()
        except Exception:
            pass
        try:
            content = page.content().lower()
        except Exception:
            pass

        # Verifica padrões de texto em título ou conteúdo
        if _SESSAO_EXPIRADA_REGEX.search(title) or _SESSAO_EXPIRADA_REGEX.search(content):
            return True

        # Verifica se há campos de login visíveis (input de usuário + senha)
        try:
            user_inputs = page.locator("input[name='username'], input[name='j_username'], #username, input[id*='username']").count()
            pass_inputs = page.locator("input[type='password'], input[name='password'], input[name='j_password'], #password").count()
            if user_inputs > 0 and pass_inputs > 0:
                # Cruza com URL ou textos para evitar falsos positivos em páginas de cadastro
                if any(fragment in url for fragment in ["login", "autentica", "sessao", "session", "logon"]):
                    return True
                if _SESSAO_EXPIRADA_REGEX.search(content):
                    return True
        except Exception:
            pass

        return False
    except Exception as e:
        aviso(f"Erro ao verificar sessão: {e}")
        # Em dúvida, assumimos que pode estar expirada para forçar reconexão
        return True


def ensure_logged_in(client) -> bool:
    """
    Verifica se o cliente está logado e, se necessário, executa reconexão.

    Args:
        client: Instância de cliente (ex: PjeClient ou SistjClient) que possua
                os atributos `page`, `verificar_sessao()` e `reconectar()`.

    Returns:
        True se estiver logado após a verificação/reconexão.
    """
    try:
        if not hasattr(client, "page") or not client.page:
            if hasattr(client, "login"):
                return client.login()
            return False

        if hasattr(client, "verificar_sessao") and client.verificar_sessao():
            info(f"Sessão expirada detectada em {type(client).__name__}, iniciando reconexão...")
            if hasattr(client, "reconectar"):
                return client.reconectar()
            elif hasattr(client, "login"):
                return client.login()
            return False

        return True
    except Exception as e:
        erro(f"Falha em ensure_logged_in: {e}")
        return False


def _is_credential_error(exc: Exception) -> bool:
    """Verifica se a exceção é relacionada a credenciais inválidas (não deve retry)."""
    msg = str(exc).lower()
    return any(err in msg for err in _CREDENTIAL_ERRORS)


def retry_on_exception(
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = (Exception,),
    max_retries: int = 3,
    backoff: int = 2,
):
    """
    Decorador de retry com backoff exponencial e reconexão automática.

    Args:
        exceptions: Exceção(s) que devem disparar retry.
        max_retries: Número máximo de tentativas (incluindo a primeira).
        backoff: Base do backoff exponencial. Tentativas aguardam backoff^(n-1) segundos.
                 Padrão 2 gera intervalos de 1s, 2s, 4s.

    Comportamento especial:
        - Se a instância (self) tiver `verificar_sessao` e `reconectar`, detecta sessão
          expirada antes de cada retry e reconecta automaticamente.
        - Erros de credenciais (401/403/etc) NÃO são retried.
        - Cada tentativa é logada.
    """
    if not isinstance(exceptions, tuple):
        exceptions = (exceptions,)

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # args[0] provavelmente é self em métodos de instância
            instance = args[0] if args else None
            func_name = func.__qualname__

            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    if _is_credential_error(exc):
                        erro(f"Erro de credenciais em {func_name}: {exc}. Não será feito retry.")
                        raise

                    if attempt >= max_retries:
                        erro(f"{func_name} falhou após {max_retries} tentativas: {exc}")
                        raise

                    # Verifica sessão expirada e tenta reconectar antes do retry
                    if (
                        instance
                        and hasattr(instance, "verificar_sessao")
                        and hasattr(instance, "reconectar")
                        and hasattr(instance, "page")
                    ):
                        try:
                            if instance.verificar_sessao():
                                info(f"Sessão expirada em {func_name}, reconectando antes do retry {attempt + 1}...")
                                reconectou = instance.reconectar()
                                if not reconectou:
                                    aviso(f"Reconexão falhou em {func_name}, prosseguindo com retry mesmo assim.")
                        except Exception as recon_err:
                            aviso(f"Erro ao verificar/reconectar em {func_name}: {recon_err}")

                    wait_time = backoff ** (attempt - 1)
                    info(f"Retry {func_name} (tentativa {attempt}/{max_retries}) em {wait_time}s após erro: {exc}")
                    time.sleep(wait_time)

        return wrapper
    return decorator
