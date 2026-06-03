"""
Automação do SISTJWEB para preenchimento da planilha de custas.

Este módulo interage com o sistema SISTJWEB (Java/JSF) do TJDFT utilizando
seletores CSS robustos com múltiplas alternativas (fallback) para lidar com
variações no DOM entre versões do sistema ou estados de renderização.

Regras de seletor aplicadas:
  1. Preferência por atributos estáveis: name, id, value.
  2. Fallback para text-match (Playwright :has-text) quando não há id/name.
  3. Timeouts configuráveis por operação crítica.
  4. Helpers centralizados para click/fill/select/check com retry automático.
"""

import re
from typing import Dict, Any, Optional, List

from playwright.sync_api import Page, Browser, TimeoutError as PlaywrightTimeout

from config import (
    SISTJ_URL,
    SCREENSHOTS_DIR,
    DEMONSTRATIVOS_DIR,
    STORAGE_STATE_SISTJ,
    HEADLESS,
)
from utils.logger import info, erro, aviso
from regras import detectar_area, obter_regras_outros_itens
from modulos.retry import retry_on_exception
from modulos.css_escape import escape_for_css
from modulos.playwright_client import PlaywrightClient
from modulos.auth_manager import AuthManager

# Importa constantes de seletores organizadas por seção do sistema
from modulos.selectors import (
    NAV_MENU_CUSTAS,
    NAV_SUBMENU_ATUALIZAR,
    NAV_BOTAO_PREENCHER,
    RADIO_PROC_ELETRONICO_SIM,
    RADIO_INSTANCIA_1,
    RADIO_INSTANCIA_2,
    INPUT_NUMERO_PROCESSO,
    BTN_CONSULTAR,
    INPUT_VALOR_CAUSA_ATUALIZADO,
    INPUT_VALOR_CAUSA,
    INPUT_DATA_DISTRIBUICAO,
    INPUT_POLO_ATIVO,
    INPUT_POLO_PASSIVO,
    SELECT_TIPO_GUIA,
    CHECK_PRO_RATA,
    BTN_ADICIONAR_AUTOR,
    INPUT_NOME_PARTE,
    INPUT_CPF_CNPJ,
    SELECT_TIPO_PARTE,
    CHECK_ISENCAO_CUSTAS,
    MAPEAMENTO_PECAS,
    SELECT_ITEM_GUIA,

    INPUT_NUMERO_FOLHAS_OUTROS,
    INPUT_VALOR_ITEM,
    INPUT_QUANTIDADE,
    INPUT_DATA_PAGAMENTO,
    INPUT_VALOR_CUSTAS_PAGAS,
    INPUT_NUMERO_GUIA,
    BTN_ADICIONAR,
    BTN_AVANCAR,
    BTN_GRAVAR,
    BTN_GRAVAR_APROVAR,
    LABEL_VALOR_TOTAL_RECOLHER,
    VALOR_TOTAL_RECOLHER_SIBLING,
)


def _formatar_data(data_iso: str) -> str:
    """Converte YYYY-MM-DD para DD/MM/AAAA."""
    if not data_iso:
        return ""
    if "T" in data_iso:
        data_iso = data_iso.split("T")[0]
    partes = data_iso.split("-")
    if len(partes) == 3:
        return f"{partes[2]}/{partes[1]}/{partes[0]}"
    return data_iso


def _resolve_locator(page: Page, selectors: List[str], timeout: int = 5000):
    """
    Tenta resolver um elemento visível usando uma lista de seletores.

    Percorre os seletores na ordem e retorna o primeiro locator que esteja
    visível na página dentro do timeout. Se nenhum for encontrado, retorna None.
    """
    for sel in selectors:
        try:
            locator = page.locator(sel)
            # Para seletores que podem retornar múltiplos elementos,
            # garantimos que pelo menos o primeiro esteja visível.
            first = locator.first
            first.wait_for(state="visible", timeout=timeout)
            return first
        except PlaywrightTimeout:
            continue
        except Exception as exc:
            aviso(f"_resolve_locator falhou para '{sel[:60]}...': {exc}")
            continue
    return None


def safe_click(page: Page, selectors: List[str], timeout: int = 5000) -> bool:
    """
    Clica em um elemento de forma resiliente.

    Args:
        page: instância do Playwright Page.
        selectors: lista de seletores CSS/text (primário + fallbacks).
        timeout: timeout em ms para cada tentativa.

    Returns:
        True se o clique ocorreu com sucesso, False caso contrário.
    """
    locator = _resolve_locator(page, selectors, timeout)
    if locator:
        locator.click(timeout=timeout)
        return True
    # Log detalhado para facilitar debug
    aviso(f"safe_click falhou para seletores: {selectors}")
    return False


def safe_fill(page: Page, selectors: List[str], value: str, timeout: int = 5000) -> bool:
    """
    Preenche um campo de input de forma resiliente.

    Limpa o campo antes de preencher (fill já limpa, mas garantimos
    via clear caso seja necessário interação adicional futura).
    """
    locator = _resolve_locator(page, selectors, timeout)
    if locator:
        locator.fill(str(value), timeout=timeout)
        return True
    aviso(f"safe_fill falhou para seletores: {selectors} | valor: {value}")
    return False


def safe_select_option(page: Page, selectors: List[str], value: str, timeout: int = 5000) -> bool:
    """
    Seleciona uma opção em um <select> de forma resiliente.
    """
    locator = _resolve_locator(page, selectors, timeout)
    if locator:
        locator.select_option(value, timeout=timeout)
        return True
    aviso(f"safe_select_option falhou para seletores: {selectors} | valor: {value}")
    return False


def safe_check(page: Page, selectors: List[str], timeout: int = 5000) -> bool:
    """
    Marca um checkbox de forma resiliente (idempotente: só marca se desmarcado).
    """
    locator = _resolve_locator(page, selectors, timeout)
    if locator:
        if not locator.is_checked():
            locator.check(timeout=timeout)
        return True
    aviso(f"safe_check falhou para seletores: {selectors}")
    return False


def safe_get_input_value(page: Page, selectors: List[str], timeout: int = 3000) -> str:
    """
    Lê o valor (input_value) de um campo de forma resiliente.
    Retorna string vazia se não encontrar.
    """
    locator = _resolve_locator(page, selectors, timeout)
    if locator:
        try:
            return locator.input_value() or ""
        except PlaywrightTimeout:
            aviso(f"Timeout ao ler input_value de seletores: {selectors}")
            return ""
        except Exception as exc:
            aviso(f"Erro ao ler input_value de seletores {selectors}: {exc}")
            return ""
    return ""


class SistjClient(PlaywrightClient):
    """Cliente de automação para o SISTJWEB (planilha de custas TJDFT)."""

    def __init__(self):
        super().__init__()
        self._auth = AuthManager(STORAGE_STATE_SISTJ, headless_default=HEADLESS)

    def garantir_autenticado(self) -> bool:
        """Verifica autenticação; se necessário, dispara fallback interativo."""
        return self._auth.verificar_e_autenticar(
            url=SISTJ_URL,
            verificar_sucesso_fn=self._esta_logado,
        )

    def login(self) -> bool:
        """Alias para garantir_autenticado() — mantido para compatibilidade."""
        return self.garantir_autenticado()

    def reautenticar_interativo(self) -> bool:
        """Força reautenticação com navegador visível."""
        return self._auth.forcar_reautenticacao_interativa(
            url=SISTJ_URL,
            verificar_sucesso_fn=self._esta_logado,
            manter_aberto_apos_login=True,
        )

    def _esta_logado(self, page: Page) -> bool:
        """Retorna True se a página indicar que o usuário está logado no SISTJWEB."""
        try:
            # Indicador 1: ausência de campos de login
            try:
                user_inputs = page.locator(
                    "input[name='j_username'], input[name='username'], #username"
                ).count()
                pass_inputs = page.locator(
                    "input[type='password'], input[name='j_password'], #password"
                ).count()
                if user_inputs == 0 and pass_inputs == 0:
                    # Sem campos de login — possivelmente logado; cruzar com outros indicadores
                    pass
                else:
                    # Campos de login presentes — provavelmente não logado
                    return False
            except Exception:
                pass

            # Indicador 2: presença de elementos da área logada
            seletores_logado = [
                "a:has-text('Custas')",
                "span:has-text('Custas')",
                "[class*='menu']",
                "#menu",
                ".menu",
            ]
            try:
                for sel in seletores_logado:
                    if page.locator(sel).count() > 0:
                        return True
            except Exception:
                pass

            # Indicador 3: URL não é página de login
            url = page.url.lower()
            if "login" not in url and "autentica" not in url:
                return True

            return False
        except Exception as exc:
            aviso(f"Erro ao verificar estado de login no SISTJWEB: {exc}")
            return False

    @retry_on_exception(
        exceptions=(PlaywrightTimeout, ConnectionError, TimeoutError),
        max_retries=3,
        backoff=2,
    )
    def preencher(self, dados: Dict[str, Any], numero_processo: str) -> Dict[str, Any]:
        """
        Preenche a planilha de custas no SISTJWEB.

        Retorna dict com:
          - screenshot_path: caminho da captura de tela.
          - valor_total_recolher: valor extraído da tela de resumo.
        """
        resultado = {"screenshot_path": "", "valor_total_recolher": ""}

        try:
            # ── Navegação: Custas > Atualizar Planilha > Preencher ──
            safe_click(self.page, NAV_MENU_CUSTAS, timeout=10000)
            safe_click(self.page, NAV_SUBMENU_ATUALIZAR, timeout=10000)
            safe_click(self.page, NAV_BOTAO_PREENCHER, timeout=10000)
            self.page.wait_for_load_state("networkidle")

            # ── Passo 1: Dados do Processo ──
            # Marca "Processo Eletrônico = Sim"
            safe_click(self.page, RADIO_PROC_ELETRONICO_SIM, timeout=5000)

            # Seleção de instância (1ª ou 2ª)
            instancia = dados.get("instancia", "")
            if "1" in instancia:
                safe_click(self.page, RADIO_INSTANCIA_1, timeout=5000)
            else:
                safe_click(self.page, RADIO_INSTANCIA_2, timeout=5000)

            # Preenche número do processo e consulta
            numero_sem_mascara = dados.get("numero_sem_mascara", "")
            safe_fill(self.page, INPUT_NUMERO_PROCESSO, numero_sem_mascara, timeout=5000)
            safe_click(self.page, BTN_CONSULTAR, timeout=5000)
            self.page.wait_for_timeout(3000)

            # Lê Valor da Causa Atualizado retornado pela consulta
            valor_causa_atualizado = safe_get_input_value(
                self.page, INPUT_VALOR_CAUSA_ATUALIZADO, timeout=3000
            )

            # Preenche Valor da Causa
            valor_causa = dados.get("valor_causa", "")
            safe_fill(self.page, INPUT_VALOR_CAUSA, valor_causa, timeout=5000)

            # Preenche Data de Distribuição (formato DD/MM/AAAA)
            data_distrib = _formatar_data(dados.get("data_distribuicao", ""))
            safe_fill(self.page, INPUT_DATA_DISTRIBUICAO, data_distrib, timeout=5000)

            # Polo Ativo
            safe_fill(self.page, INPUT_POLO_ATIVO, dados.get("polo_ativo", ""), timeout=5000)

            # Polo Passivo (default "Não Há" para evitar campo vazio)
            polo_passivo = dados.get("polo_passivo", "Não Há")
            if not polo_passivo:
                polo_passivo = "Não Há"
            safe_fill(self.page, INPUT_POLO_PASSIVO, polo_passivo, timeout=5000)

            # ── Passo 2: Custas ──
            # Seleciona tipo de guia conforme instância
            if "1" in instancia:
                safe_select_option(
                    self.page, SELECT_TIPO_GUIA, "Guia Final - 1ª Instância", timeout=5000
                )
            else:
                safe_select_option(
                    self.page, SELECT_TIPO_GUIA, "Guia Final - 2ª Instância", timeout=5000
                )

            # Marca pro-rata se houver mais de um sucumbente
            sucumbentes = dados.get("sucumbentes", [])
            if len(sucumbentes) > 1:
                safe_check(self.page, CHECK_PRO_RATA, timeout=5000)

            # Adiciona partes (autores/requeridos)
            for suc in sucumbentes:
                if suc.get("is_autor"):
                    # Botão específico para adicionar autor(es)
                    safe_click(self.page, BTN_ADICIONAR_AUTOR, timeout=5000)
                else:
                    safe_fill(self.page, INPUT_NOME_PARTE, suc.get("nome", ""), timeout=5000)
                    safe_fill(self.page, INPUT_CPF_CNPJ, suc.get("cpf_cnpj", ""), timeout=5000)
                    safe_select_option(
                        self.page, SELECT_TIPO_PARTE, suc.get("tipo", "Requerido"), timeout=5000
                    )
                    safe_click(self.page, BTN_ADICIONAR, timeout=5000)

                # Isenção de custas (suspensão de exigibilidade)
                if dados.get("suspensao_exigibilidade"):
                    safe_check(self.page, CHECK_ISENCAO_CUSTAS, timeout=5000)

            # ── Passo 3: Peças Processuais (IDs) ──
            # Cada peça é uma linha de tabela onde cada linha contém o label e um input.
            # O seletor primário usa :has-text para localizar a linha (tr) e depois o input.
            # Fallbacks usam id ou name quando previsíveis.
            for campo_id, seletores_peca in MAPEAMENTO_PECAS.items():
                valor = dados.get(campo_id, "")
                if valor:
                    try:
                        # Tenta preencher usando a lista completa de seletores da peça
                        safe_fill(self.page, seletores_peca, str(valor), timeout=3000)
                    except PlaywrightTimeout:
                        aviso(f"Timeout ao preencher peça {campo_id} — peça opcional, prosseguindo.")
                    except Exception as exc:
                        aviso(f"Erro ao preencher peça {campo_id}: {exc} — peça opcional, prosseguindo.")

            # ── Passo 4: Outros Itens ──
            area = detectar_area(dados.get("classe", ""), dados.get("feito", ""))
            regras = obter_regras_outros_itens(area)

            for item in regras:
                # Seleciona o item no dropdown "itemGuia"
                safe_select_option(self.page, SELECT_ITEM_GUIA, item["item_guia"], timeout=5000)
                self.page.wait_for_timeout(1000)

                # Aguarda e seleciona o radio de cálculo correspondente
                valor_radio = item["item_calculo"]
                valor_escapado = escape_for_css(valor_radio)
                seletores_radio = [
                    f"input[value='{valor_escapado}'][name*='itemCalculo']",
                    f"input[value='{valor_escapado}'][name*='item']",
                    f"input[type='radio'][value='{valor_escapado}']",
                ]
                safe_click(self.page, seletores_radio, timeout=5000)

                # Campos condicionais
                if item.get("usa_ids_oficios") and dados.get("ids_oficios"):
                    safe_fill(
                        self.page,
                        INPUT_NUMERO_FOLHAS_OUTROS,
                        dados["ids_oficios"],
                        timeout=3000,
                    )

                if item.get("usa_valor_causa_atualizado") and valor_causa_atualizado:
                    safe_fill(
                        self.page, INPUT_VALOR_ITEM, valor_causa_atualizado, timeout=3000
                    )

                safe_fill(
                    self.page, INPUT_QUANTIDADE, str(item.get("quantidade", 1)), timeout=3000
                )
                safe_click(self.page, BTN_ADICIONAR, timeout=5000)
                self.page.wait_for_timeout(500)

            # ── Passo 5: Custas Pagas ──
            for cp in dados.get("custas_pagas", []):
                data_pag = _formatar_data(cp.get("data", ""))
                safe_fill(self.page, INPUT_DATA_PAGAMENTO, data_pag, timeout=3000)
                safe_fill(self.page, INPUT_VALOR_CUSTAS_PAGAS, cp.get("valor", ""), timeout=3000)
                safe_fill(self.page, INPUT_NUMERO_GUIA, cp.get("numero_guia", ""), timeout=3000)
                safe_click(self.page, BTN_ADICIONAR, timeout=5000)
                self.page.wait_for_timeout(500)

            # ── Passo 6: Avançar e capturar resultado ──
            safe_click(self.page, BTN_AVANCAR, timeout=10000)
            self.page.wait_for_timeout(3000)

            # Extrai "Valor Total a Recolher"
            try:
                # Estratégia 1: locator via texto + sibling
                sibling_locator = self.page.locator(VALOR_TOTAL_RECOLHER_SIBLING[0])
                if sibling_locator.count() > 0:
                    resultado["valor_total_recolher"] = sibling_locator.first.inner_text(timeout=5000)
            except PlaywrightTimeout:
                aviso("Timeout ao extrair valor_total_recolher via sibling.")
            except Exception as exc:
                aviso(f"Erro ao extrair valor_total_recolher via sibling: {exc}")

            # Estratégia 2: regex no HTML bruto como último recurso
            if not resultado["valor_total_recolher"]:
                try:
                    html = self.page.content()
                    m = re.search(
                        r"Valor Total a Recolher[\s:]*R?\$?\s*([\d.,]+)", html, re.IGNORECASE
                    )
                    if m:
                        resultado["valor_total_recolher"] = m.group(1)
                except Exception as exc:
                    aviso(f"Erro ao extrair valor_total_recolher via regex: {exc}")

            # Screenshot de resumo
            screenshot_path = SCREENSHOTS_DIR / f"{numero_processo}_sistjweb.png"
            self.page.screenshot(path=str(screenshot_path), full_page=True)
            resultado["screenshot_path"] = str(screenshot_path)

            # Grava a planilha
            safe_click(self.page, BTN_GRAVAR, timeout=10000)
            self.page.wait_for_timeout(2000)

            info(f"Planilha SISTJWEB preenchida para {numero_processo}.")
            return resultado

        except Exception as e:
            erro(f"Falha ao preencher SISTJWEB para {numero_processo}: {e}")
            raise

    @retry_on_exception(
        exceptions=(PlaywrightTimeout, ConnectionError, TimeoutError),
        max_retries=3,
        backoff=2,
    )
    def gravar_e_aprovar(self, numero_processo: str) -> str:
        """
        Navega até o processo salvo e clica 'Gravar e Aprovar'.

        Retorna o caminho do PDF baixado.
        """
        try:
            self.page.goto(SISTJ_URL, wait_until="networkidle")

            # Reabre o fluxo: Custas > Atualizar Planilha > Preencher
            safe_click(self.page, NAV_MENU_CUSTAS, timeout=10000)
            safe_click(self.page, NAV_SUBMENU_ATUALIZAR, timeout=10000)
            safe_click(self.page, NAV_BOTAO_PREENCHER, timeout=10000)

            # Consulta o processo previamente salvo
            safe_fill(self.page, INPUT_NUMERO_PROCESSO, numero_processo, timeout=5000)
            safe_click(self.page, BTN_CONSULTAR, timeout=5000)
            self.page.wait_for_timeout(2000)

            # Abre o processo na lista de resultados
            try:
                self.page.get_by_text(numero_processo, exact=True).click(timeout=5000)
            except PlaywrightTimeout:
                # Fallback com seletor CSS escapado
                numero_escapado = escape_for_css(numero_processo)
                self.page.locator(f"td:has-text('{numero_escapado}'), a:has-text('{numero_escapado}')").first.click(timeout=5000)
            self.page.wait_for_timeout(2000)

            # Clica em Gravar e Aprovar, capturando o download do PDF
            with self.page.expect_download() as download_info:
                safe_click(self.page, BTN_GRAVAR_APROVAR, timeout=10000)
            download = download_info.value

            caminho_pdf = str(DEMONSTRATIVOS_DIR / f"{numero_processo}.pdf")
            download.save_as(caminho_pdf)

            info(f"Demonstrativo baixado: {caminho_pdf}")
            return caminho_pdf

        except Exception as e:
            erro(f"Falha ao gravar/aprovar no SISTJWEB: {e}")
            raise
