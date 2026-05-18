"""
Automação do PJE TJDFT.
- Login com tratamento de iframe
- Coleta de lista de processos por etiqueta
- Coleta de documentos e textos (com visualizador em iframe/popup)
- Anexar demonstrativo PDF

Seletores baseados na estrutura RichFaces/JSF do PJE:
  • tabelas: .rich-table, .rich-table-row, .rich-table-cell
  • menus: .menu-lateral, .item-menu, links com textos fixos
  • formulários: inputs com name/id gerados pelo JSF (ex: formulario:username)
"""
import json
import os
import re
from typing import List, Dict, Any, Optional, Tuple
from playwright.sync_api import Page, Browser, FrameLocator, TimeoutError as PlaywrightTimeout

from config import (
    PJE_URL,
    PJE_ETIQUETA,
    STORAGE_STATE_PJE,
    HEADLESS,
)
from utils.logger import info, erro, aviso
from banco import db
from modulos.retry import retry_on_exception
from modulos.playwright_client import PlaywrightClient
from modulos.auth_manager import AuthManager
from modulos.css_escape import escape_for_css


# ─────────────────────────────────────────────────────────────
# CONSTANTES / UTILIDADES
# ─────────────────────────────────────────────────────────────

# Regex CNJ robusto: aceita formatado (NNNNNNN-NN.NNNN.N.NN.NNNN) ou
# cru (20 dígitos). Captura grupos para reconstrução se necessário.
_RE_CNJ_FORMATADO = re.compile(
    r"\b(\d{7})[-.]?(\d{2})[-.]?(\d{4})[-.]?(\d)[-.]?(\d{2})[-.]?(\d{4})\b"
)
_RE_CNJ_CRU = re.compile(r"\b(\d{20})\b")


def _formatar_numero_processo(numero: str) -> str:
    """Remove formatação do número CNJ, retornando 20 dígitos."""
    return re.sub(r"\D", "", numero)


def _extrair_numeros_processo(html: str) -> List[str]:
    """Extrai todos os números CNJ do HTML (formatados ou não)."""
    encontrados: set = set()
    # Tenta primeiro o padrão formatado
    for m in _RE_CNJ_FORMATADO.finditer(html):
        cru = "".join(m.groups())
        if len(cru) == 20:
            encontrados.add(cru)
    # Fallback: números crús de 20 dígitos
    for m in _RE_CNJ_CRU.finditer(html):
        cru = m.group(1)
        if cru not in encontrados:
            encontrados.add(cru)
    return sorted(encontrados)


# ─────────────────────────────────────────────────────────────
# FUNÇÕES AUXILIARES RESILIENTES
# ─────────────────────────────────────────────────────────────

def _tentar_seletores(page_or_locator, seletores: List[str], **kwargs) -> bool:
    """
    Tenta cada seletor da lista até encontrar um elemento visível.
    Retorna True se algum for encontrado.
    """
    for sel in seletores:
        try:
            if page_or_locator.locator(sel).first.is_visible(timeout=2000):
                return True
        except PlaywrightTimeout:
            continue
        except Exception as exc:
            aviso(f"_tentar_seletores falhou para '{sel[:60]}...': {exc}")
            continue
    return False


def _safe_click(page: Page, seletores: List[str], timeout: int = 10000) -> bool:
    """
    Clica no primeiro seletor visível da lista.
    Útil quando o DOM varia entre versões do PJE.
    """
    for sel in seletores:
        try:
            loc = page.locator(sel)
            if loc.count() > 0:
                loc.first.click(timeout=timeout)
                return True
        except PlaywrightTimeout:
            continue
        except Exception as exc:
            aviso(f"_safe_click falhou para '{sel[:60]}...': {exc}")
            continue
    return False


def _safe_fill(page: Page, seletores: List[str], valor: str, timeout: int = 10000) -> bool:
    """Preenche o primeiro campo visível encontrado entre os seletores."""
    for sel in seletores:
        try:
            loc = page.locator(sel)
            if loc.count() > 0 and loc.first.is_visible(timeout=2000):
                loc.first.fill(valor, timeout=timeout)
                return True
        except PlaywrightTimeout:
            continue
        except Exception as exc:
            aviso(f"_safe_fill falhou para '{sel[:60]}...': {exc}")
            continue
    return False


def _safe_wait(page: Page, seletores: List[str], timeout: int = 15000) -> bool:
    """Aguarda o primeiro seletor da lista aparecer."""
    for sel in seletores:
        try:
            page.wait_for_selector(sel, timeout=timeout)
            return True
        except PlaywrightTimeout:
            continue
    return False


def _clicar_por_texto_exato(page: Page, texto: str, timeout: int = 10000) -> bool:
    """
    Clica em elemento cujo texto exato corresponda.
    Usa get_by_text como primeira estratégia (seguro contra injeção CSS).
    Fallback com seletores CSS escapados.
    """
    try:
        page.get_by_text(texto, exact=True).click(timeout=timeout)
        return True
    except PlaywrightTimeout:
        pass
    except Exception as exc:
        aviso(f"get_by_text falhou para '{texto[:60]}...': {exc}")

    texto_escapado = escape_for_css(texto)
    estrategias = [
        f"a:has-text('{texto_escapado}')",
        f"span:has-text('{texto_escapado}')",
        f"div:has-text('{texto_escapado}')",
        f"td:has-text('{texto_escapado}')",
        f"li:has-text('{texto_escapado}')",
        f"[role='link']:has-text('{texto_escapado}')",
        f"[role='button']:has-text('{texto_escapado}')",
    ]
    return _safe_click(page, estrategias, timeout=timeout)


def _entrar_iframe_login(page: Page, timeout: int = 15000) -> Optional[Page]:
    """
    O PJE TJDFT frequentemente carrega o formulário de login dentro de um iframe.
    Esta função detecta e retorna o frame (Page/FrameLocator) correto para
    interagir com os campos de autenticação.
    """
    # Primeiro verifica se o campo já está na página principal
    try:
        if page.locator("input[name='username'], #username").count() > 0:
            return page
    except PlaywrightTimeout:
        pass
    except Exception as exc:
        aviso(f"Erro ao verificar página principal no iframe login: {exc}")

    # Procura iframe de login por id ou name parciais
    iframe_seletores = [
        "iframe[id*='login']",
        "iframe[name*='login']",
        "iframe[src*='login']",
        "iframe[src*='autentica']",
        "iframe",  # fallback: pega o primeiro iframe
    ]
    for sel in iframe_seletores:
        try:
            loc = page.locator(sel)
            if loc.count() > 0:
                iframe = loc.first.content_frame()
                if iframe and iframe.locator("input[name='username'], #username").count() > 0:
                    return iframe
        except PlaywrightTimeout:
            continue
        except Exception as exc:
            aviso(f"Erro ao inspecionar iframe '{sel[:40]}...': {exc}")
            continue
    return page  # fallback: trabalha na página mesmo assim


def _aguardar_e_clicar_menu(page: Page, texto_menu: str, timeout: int = 10000) -> bool:
    """
    Alguns menus do PJE exigem hover ou aguardam animação antes do click.
    Tenta get_by_text (seguro) primeiro, depois seletores CSS escapados.
    """
    try:
        loc = page.get_by_text(texto_menu, exact=True)
        loc.scroll_into_view_if_needed(timeout=timeout)
        loc.click(timeout=timeout)
        return True
    except PlaywrightTimeout:
        pass
    except Exception as exc:
        aviso(f"get_by_text falhou no menu '{texto_menu[:60]}...': {exc}")

    texto_escapado = escape_for_css(texto_menu)
    seletores = [
        f"a:has-text('{texto_escapado}')",
        f"span:has-text('{texto_escapado}')",
        f"li:has-text('{texto_escapado}') >> a",
        f"[class*='menu']:has-text('{texto_escapado}')",
    ]
    for sel in seletores:
        try:
            loc = page.locator(sel).first
            loc.scroll_into_view_if_needed(timeout=timeout)
            loc.click(timeout=timeout)
            return True
        except PlaywrightTimeout:
            continue
        except Exception as exc:
            aviso(f"_aguardar_e_clicar_menu falhou para '{sel[:60]}...': {exc}")
            continue
    return False


# ─────────────────────────────────────────────────────────────
# PJE CLIENT
# ─────────────────────────────────────────────────────────────

class PjeClient(PlaywrightClient):
    def __init__(self):
        super().__init__()
        self._auth = AuthManager(STORAGE_STATE_PJE, headless_default=HEADLESS)

    def garantir_autenticado(self) -> bool:
        """Verifica autenticação; se necessário, dispara fallback interativo."""
        return self._auth.verificar_e_autenticar(
            url=PJE_URL,
            verificar_sucesso_fn=self._esta_logado,
            accept_downloads=True,
        )

    def login(self) -> bool:
        """Alias para garantir_autenticado() — mantido para compatibilidade."""
        return self.garantir_autenticado()

    def _esta_logado(self, page: Page) -> bool:
        """Retorna True se a página indicar que o usuário está logado no PJe."""
        try:
            # Verifica login: indicadores configuráveis via env var + seletores genéricos
            _indicadores_raw = os.getenv("PJE_INDICADORES_SUCESSO", "")
            indicadores_texto = []
            if _indicadores_raw:
                try:
                    indicadores_texto = json.loads(_indicadores_raw)
                    if not isinstance(indicadores_texto, list):
                        indicadores_texto = []
                except json.JSONDecodeError:
                    aviso(f"PJE_INDICADORES_SUCESSO inválido (não é JSON list): {_indicadores_raw[:100]}")
                    indicadores_texto = []

            if indicadores_texto:
                for texto in indicadores_texto:
                    try:
                        if page.get_by_text(texto, exact=True).count() > 0:
                            return True
                    except PlaywrightTimeout:
                        continue
                    except Exception as exc:
                        aviso(f"Erro ao verificar indicador de login '{texto[:40]}...': {exc}")
                        continue

            # Se não há indicadores textuais configurados, ou nenhum bateu,
            # verifica seletores genéricos de DOM (menu, avatar, botão sair)
            seletores_genericos = [
                ".nome-usuario",
                ".usuario-logado",
                "[class*='menu-lateral']",
                "#menuPrincipal",
            ]
            try:
                logado_dom = any(
                    page.locator(sel).count() > 0 for sel in seletores_genericos
                )
                if logado_dom:
                    return True
            except PlaywrightTimeout:
                pass
            except Exception as exc:
                aviso(f"Erro ao verificar indicadores genéricos de login: {exc}")

            # Último recurso: verifica se a URL mudou para algo diferente de login
            if "login" not in page.url.lower():
                return True

            return False
        except Exception as exc:
            aviso(f"Erro ao verificar estado de login no PJe: {exc}")
            return False

    # ─────────────────────────────────────────────────────────
    # COLETA DE PROCESSOS POR ETIQUETA
    # ─────────────────────────────────────────────────────────
    @retry_on_exception(
        exceptions=(PlaywrightTimeout, ConnectionError, TimeoutError),
        max_retries=3,
        backoff=2,
    )
    def coletar_lista_processos(self) -> List[str]:
        """Navega até a etiqueta e extrai números de processo."""
        try:
            # Menu: Meu Perfil -> Núcleo Permanente de Cálculos
            # Usa _aguardar_e_clicar_menu porque o PJE às vezes exige scroll
            _aguardar_e_clicar_menu(self.page, "Meu Perfil", timeout=12000)
            self.page.wait_for_timeout(1000)
            _aguardar_e_clicar_menu(self.page, "Núcleo Permanente de Cálculos", timeout=12000)
            self.page.wait_for_timeout(1000)

            # Tarefas -> Incluir Cálculo
            _aguardar_e_clicar_menu(self.page, "Tarefas", timeout=12000)
            self.page.wait_for_timeout(1000)
            _aguardar_e_clicar_menu(self.page, "Incluir Cálculo", timeout=12000)
            self.page.wait_for_timeout(2000)

            # Etiquetas -> clica na etiqueta configurada
            # O PJE pode renderizar etiquetas como links, spans ou badges
            if not _clicar_por_texto_exato(self.page, PJE_ETIQUETA):
                aviso(f"Etiqueta '{PJE_ETIQUETA}' não encontrada via texto; tentando seletores genéricos.")
                etiqueta_escapada = escape_for_css(PJE_ETIQUETA)
                _safe_click(self.page, [f"a:has-text('{etiqueta_escapada}')", f"span:has-text('{etiqueta_escapada}')"])

            # Aguarda a grade/tabela de processos carregar
            seletores_tabela = [
                ".rich-table",           # RichFaces
                "table.rich-table",
                ".processo",
                ".numero-processo",
                "table[class*='processo']",
                "tbody tr",              # fallback genérico
            ]
            _safe_wait(self.page, seletores_tabela, timeout=20000)
            self.page.wait_for_timeout(3000)

            # Extrai números CNJ do HTML inteiro (mais confiável que iterar linhas)
            html = self.page.content()
            numeros = _extrair_numeros_processo(html)

            info(f"Encontrados {len(numeros)} processos na etiqueta '{PJE_ETIQUETA}'.")
            return numeros
        except Exception as e:
            erro(f"Falha ao coletar lista de processos no PJE: {e}")
            return []

    # ─────────────────────────────────────────────────────────
    # COLETA DE DOCUMENTOS
    # ─────────────────────────────────────────────────────────
    @retry_on_exception(
        exceptions=(PlaywrightTimeout, ConnectionError, TimeoutError),
        max_retries=3,
        backoff=2,
    )
    def coletar_documentos(self, numero_processo: str) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
        """
        Acessa o processo e coleta documentos.
        Retorna (lista_docs, dict_textos).
        """
        docs: List[Dict[str, Any]] = []
        textos: Dict[str, str] = {}
        try:
            # Clica no número do processo (pode estar em link, td ou span)
            numero_escapado = escape_for_css(numero_processo)
            seletores_processo = [
                f"a:has-text('{numero_escapado}')",
                f"td:has-text('{numero_escapado}')",
                f"span:has-text('{numero_escapado}')",
            ]
            if not _safe_click(self.page, seletores_processo, timeout=15000):
                aviso(f"Não foi possível clicar no processo {numero_processo}")
                return docs, textos

            self.page.wait_for_load_state("networkidle")
            self.page.wait_for_timeout(3000)

            # Aguarda tabela de documentos
            seletores_tabela_docs = [
                ".rich-table",                       # tabela RichFaces
                "table.rich-table",
                ".documentos",
                "#tabelaDocumentos",
                "table[id*='documento']",
                "table",                             # fallback
            ]
            _safe_wait(self.page, seletores_tabela_docs, timeout=20000)

            # Extrai linhas da tabela — prioriza rich-table-row, depois tbody tr
            linhas = self.page.locator(".rich-table-row, table tbody tr, .documento-item").all()
            for linha in linhas:
                try:
                    # Células podem ter classe .rich-table-cell ou ser <td> comuns
                    celulas = linha.locator(".rich-table-cell, td").all_inner_texts()
                except PlaywrightTimeout:
                    continue
                except Exception as exc:
                    aviso(f"Erro ao extrair células de linha da tabela de documentos: {exc}")
                    continue
                if len(celulas) >= 4:
                    doc_id = re.sub(r"\D", "", celulas[0]) or ""
                    data_assinatura = celulas[1].strip()
                    nome_doc = celulas[2].strip()
                    tipo = celulas[3].strip()
                    docs.append({
                        "doc_id": doc_id,
                        "tipo": tipo,
                        "data_assinatura": data_assinatura,
                        "nome": nome_doc,
                    })

            # Lê conteúdo de documentos relevantes
            for doc in docs:
                if doc["tipo"] in ("Sentença", "Decisão", "Comprovante de Pagamento de Custas", "Despacho"):
                    try:
                        # Clica no nome do documento
                        _clicar_por_texto_exato(self.page, doc["nome"])
                        self.page.wait_for_timeout(3000)

                        texto = ""
                        # Estratégia 1: iframe de visualização (PDF ou HTML)
                        iframe_seletores = [
                            "iframe[id*='visualiz']",
                            "iframe[name*='visualiz']",
                            "iframe[id*='doc']",
                            "iframe[src*='visualiz']",
                            "iframe",  # último recurso
                        ]
                        for if_sel in iframe_seletores:
                            try:
                                if self.page.locator(if_sel).count() > 0:
                                    iframe = self.page.frame_locator(if_sel).first
                                    # Tenta body ou embed/pdf
                                    texto = iframe.locator("body").inner_text(timeout=8000)
                                    if texto.strip():
                                        break
                            except PlaywrightTimeout:
                                continue
                            except Exception as exc:
                                aviso(f"Erro ao ler iframe '{if_sel[:40]}...' do doc {doc['doc_id']}: {exc}")
                                continue

                        # Estratégia 2: popup / nova aba (menos comum)
                        if not texto.strip():
                            # O PJE às vezes abre visualizador em modal/popup
                            modal_seletores = [
                                ".modal-body",
                                "[role='dialog']",
                                "#visualizadorDocumento",
                                "[class*='visualizador']",
                            ]
                            for m_sel in modal_seletores:
                                try:
                                    if self.page.locator(m_sel).count() > 0:
                                        texto = self.page.locator(m_sel).first.inner_text(timeout=8000)
                                        if texto.strip():
                                            break
                                except PlaywrightTimeout:
                                    continue
                                except Exception as exc:
                                    aviso(f"Erro ao ler modal '{m_sel[:40]}...' do doc {doc['doc_id']}: {exc}")
                                    continue

                        # Estratégia 3: conteúdo direto na página
                        if not texto.strip():
                            texto = self.page.locator("body").inner_text()

                        textos[doc["doc_id"]] = texto.strip()

                        # Volta para lista de documentos
                        self.page.go_back()
                        self.page.wait_for_load_state("networkidle")
                        self.page.wait_for_timeout(2000)
                    except (PlaywrightTimeout, TimeoutError) as exc:
                        aviso(f"Timeout ao ler documento {doc['doc_id']} ({doc['nome']}): {exc}")
                    except Exception as exc:
                        erro(f"Erro inesperado ao ler documento {doc['doc_id']} ({doc['nome']}): {exc}")

            info(f"Coletados {len(docs)} documentos do processo {numero_processo}.")
            return docs, textos
        except Exception as e:
            erro(f"Falha ao coletar documentos de {numero_processo}: {e}")
            return docs, textos

    # ─────────────────────────────────────────────────────────
    # BAIXAR DOCUMENTO PDF
    # ─────────────────────────────────────────────────────────
    @retry_on_exception(
        exceptions=(PlaywrightTimeout, ConnectionError, TimeoutError),
        max_retries=2,
        backoff=2,
    )
    def baixar_documento_pdf(self, doc_id: str, caminho_destino: str) -> bool:
        """Baixa o PDF de um documento específico do processo no PJe.

        Assume que a página atual exibe a tabela de documentos do processo.
        Localiza a linha do documento pelo doc_id, clica no link de download
        e salva o arquivo em ``caminho_destino``.

        Args:
            doc_id: Identificador do documento (ex: "206426308").
            caminho_destino: Caminho absoluto onde o PDF será salvo.

        Returns:
            True se o download foi bem-sucedido, False caso contrário.
        """
        try:
            # Localiza a linha da tabela que contenha o doc_id
            # O PJe usa .rich-table-row ou tbody tr; tentamos encontrar
            # uma linha cujo texto contenha o doc_id.
            linhas = self.page.locator(".rich-table-row, table tbody tr, .documento-item").all()
            linha_alvo = None
            for linha in linhas:
                try:
                    texto_linha = linha.inner_text(timeout=3000)
                    if doc_id in texto_linha:
                        linha_alvo = linha
                        break
                except Exception:
                    continue

            if linha_alvo is None:
                aviso(f"Documento {doc_id} não encontrado na tabela para download.")
                return False

            # Dentro da linha, procura links (a) ou elementos clicáveis.
            # Prioriza links que pareçam download ou o próprio doc_id.
            seletores_link = [
                "a[href*='download']",
                "a[onclick*='download']",
                "a",
                "[role='link']",
                "span[onclick]",
            ]
            for sel in seletores_link:
                try:
                    links = linha_alvo.locator(sel).all()
                    for link in links:
                        if not link.is_visible():
                            continue
                        with self.page.expect_download(timeout=15000) as download_info:
                            link.click(timeout=10000)
                        download = download_info.value
                        download.save_as(caminho_destino)
                        info(f"PDF do documento {doc_id} baixado em {caminho_destino}.")
                        return True
                except PlaywrightTimeout:
                    continue
                except Exception as exc:
                    aviso(f"Tentativa de download falhou para seletor '{sel}': {exc}")
                    continue

            aviso(f"Nenhum link clicável encontrado para o documento {doc_id}.")
            return False

        except Exception as exc:
            aviso(f"Erro ao baixar PDF do documento {doc_id}: {exc}")
            return False

        return False

    # ─────────────────────────────────────────────────────────
    # ANEXAR DEMONSTRATIVO
    # ─────────────────────────────────────────────────────────
    @retry_on_exception(
        exceptions=(PlaywrightTimeout, ConnectionError, TimeoutError),
        max_retries=3,
        backoff=2,
    )
    def anexar_demonstrativo(self, numero_processo: str, caminho_pdf: str) -> bool:
        """Anexa o PDF do demonstrativo no processo."""
        try:
            # Recarrega a URL base e navega até o processo
            self.page.goto(PJE_URL, wait_until="networkidle")
            self.page.wait_for_timeout(2000)

            numero_escapado = escape_for_css(numero_processo)
            seletores_processo = [
                f"a:has-text('{numero_escapado}')",
                f"td:has-text('{numero_escapado}')",
                f"span:has-text('{numero_escapado}')",
            ]
            if not _safe_click(self.page, seletores_processo, timeout=15000):
                raise RuntimeError(f"Processo {numero_processo} não encontrado para anexação.")

            self.page.wait_for_timeout(3000)

            # Botão "Anexar" ou "Anexar Documento"
            seletores_anexar = [
                "a:has-text('Anexar')",
                "button:has-text('Anexar')",
                "a:has-text('Anexar Documento')",
                "button:has-text('Anexar Documento')",
                "input[value*='Anexar']",
            ]
            if not _safe_click(self.page, seletores_anexar, timeout=15000):
                raise RuntimeError("Botão Anexar não encontrado.")

            # Input file (pode estar em modal ou na página)
            seletores_file = [
                "input[type='file']",
                "input[id*='arquivo']",
                "input[name*='arquivo']",
                "input[id*='file']",
                "input[name*='file']",
            ]
            anexado = False
            for sel in seletores_file:
                try:
                    loc = self.page.locator(sel)
                    if loc.count() > 0:
                        loc.first.set_input_files(caminho_pdf)
                        anexado = True
                        break
                except PlaywrightTimeout:
                    continue
                except Exception as exc:
                    aviso(f"Erro ao localizar input file para upload: {exc}")
                    continue
            if not anexado:
                raise RuntimeError("Campo de upload de arquivo não encontrado.")

            # Confirma upload — tenta get_by_text (seguro) primeiro, depois seletores CSS
            confirmado = False
            for texto_btn in ("Confirmar", "Enviar", "Salvar"):
                try:
                    self.page.get_by_text(texto_btn, exact=True).click(timeout=5000)
                    confirmado = True
                    break
                except PlaywrightTimeout:
                    continue
                except Exception as exc:
                    aviso(f"get_by_text falhou para botão '{texto_btn}': {exc}")
            if not confirmado:
                seletores_confirmar = [
                    "button:has-text('Confirmar')",
                    "input[value='Confirmar']",
                    "button:has-text('Enviar')",
                    "input[value='Enviar']",
                    "button:has-text('Salvar')",
                ]
                _safe_click(self.page, seletores_confirmar, timeout=15000)
            self.page.wait_for_timeout(3000)

            info(f"Demonstrativo anexado ao processo {numero_processo}.")
            return True
        except Exception as e:
            erro(f"Falha ao anexar demonstrativo em {numero_processo}: {e}")
            return False
