"""
Automação do SISTJWEB para preenchimento da planilha de custas.
"""
import re
from typing import Dict, Any, Optional
from playwright.sync_api import sync_playwright, Page, Browser, TimeoutError as PlaywrightTimeout

from config import SISTJ_URL, SISTJ_USUARIO, SISTJ_SENHA, HEADLESS, TIMEOUT_PADRAO, SCREENSHOTS_DIR, DEMONSTRATIVOS_DIR
from utils.logger import info, erro, aviso
from regras import detectar_area, obter_regras_outros_itens


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


class SistjClient:
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self._playwright = None

    def iniciar(self):
        self._playwright = sync_playwright().start()
        self.browser = self._playwright.chromium.launch(headless=HEADLESS)
        context = self.browser.new_context(viewport={"width": 1920, "height": 1080})
        self.page = context.new_page()
        self.page.set_default_timeout(TIMEOUT_PADRAO)

    def fechar(self):
        if self.browser:
            self.browser.close()
        if self._playwright:
            self._playwright.stop()

    def login(self) -> bool:
        if not self.page:
            self.iniciar()
        try:
            self.page.goto(SISTJ_URL, wait_until="networkidle")
            self.page.fill("input[name='j_username'], #username", SISTJ_USUARIO)
            self.page.fill("input[name='j_password'], #password", SISTJ_SENHA)
            self.page.click("input[type='submit'], #btnLogin")
            self.page.wait_for_load_state("networkidle")
            self.page.wait_for_timeout(3000)
            info("Login SISTJWEB realizado com sucesso.")
            return True
        except Exception as e:
            erro(f"Falha no login SISTJWEB: {e}")
            return False

    def preencher(self, dados: Dict[str, Any], numero_processo: str) -> Dict[str, Any]:
        """
        Preenche a planilha de custas no SISTJWEB.
        Retorna dict com screenshot_path e valor_total_recolher.
        """
        resultado = {"screenshot_path": "", "valor_total_recolher": ""}

        try:
            self.page.click("text='Custas'", timeout=10000)
            self.page.click("text='Atualizar Planilha da Contadoria'", timeout=10000)
            self.page.click("text='Preencher'", timeout=10000)
            self.page.wait_for_load_state("networkidle")

            # Passo 1: Dados do Processo
            self.page.click("input[type='radio'][value='Sim'], #processoEletronicoSim", timeout=5000)

            instancia = dados.get("instancia", "")
            if "1" in instancia:
                self.page.click("input[value='1'], #instancia1", timeout=5000)
            else:
                self.page.click("input[value='2'], #instancia2", timeout=5000)

            numero_sem_mascara = dados.get("numero_sem_mascara", "")
            self.page.fill("input[name='numeroProcesso'], #numero", numero_sem_mascara)
            self.page.click("text='Consultar'", timeout=5000)
            self.page.wait_for_timeout(3000)

            # Lê Valor da Causa Atualizado da tela
            valor_causa_atualizado = ""
            try:
                valor_el = self.page.locator("input[name='valorCausaAtualizado'], #valorCausaAtualizado")
                valor_causa_atualizado = valor_el.input_value() or ""
            except Exception:
                pass

            valor_causa = dados.get("valor_causa", "")
            self.page.fill("input[name='valorCausa'], #valorCausa", valor_causa)

            data_distrib = _formatar_data(dados.get("data_distribuicao", ""))
            self.page.fill("input[name='dataDistribuicao'], #dataDistribuicao", data_distrib)

            self.page.fill("input[name='poloAtivo'], #poloAtivo", dados.get("polo_ativo", ""))

            polo_passivo = dados.get("polo_passivo", "Não Há")
            if not polo_passivo:
                polo_passivo = "Não Há"
            self.page.fill("input[name='poloPassivo'], #poloPassivo", polo_passivo)

            # Passo 2: Custas
            if "1" in instancia:
                self.page.select_option("select[name='tipoGuia'], #tipoGuia", "Guia Final - 1ª Instância")
            else:
                self.page.select_option("select[name='tipoGuia'], #tipoGuia", "Guia Final - 2ª Instância")

            sucumbentes = dados.get("sucumbentes", [])
            if len(sucumbentes) > 1:
                self.page.check("input[name='proRata'], #proRata")

            for suc in sucumbentes:
                if suc.get("is_autor"):
                    self.page.click("text='Adicionar autor(es)'", timeout=5000)
                else:
                    self.page.fill("input[name='nomeParte'], #nomeParte", suc.get("nome", ""))
                    self.page.fill("input[name='cpfCnpj'], #cpfCnpj", suc.get("cpf_cnpj", ""))
                    self.page.select_option("select[name='tipoParte'], #tipoParte", suc.get("tipo", "Requerido"))
                    self.page.click("text='Adicionar'", timeout=5000)

                if dados.get("suspensao_exigibilidade"):
                    self.page.check("input[name='isencaoCustas'], #isencaoCustas")

            # Passo 3: Peças Processuais (IDs)
            mapeamento_pecas = {
                "ids_oficios": "Ofícios",
                "ids_alvaras": "Alvarás",
                "ids_traslados": "Traslados",
                "ids_mandados": "Mandados",
                "ids_cartas_sentenca": "Cartas de Sentença",
                "ids_ar": "AR",
                "ids_armp": "AR/MP",
                "ids_circunscricao_origem": "Circunscrição de Origem",
                "ids_outra_circunscricao": "Outra Circunscrição",
            }

            for campo_id, label in mapeamento_pecas.items():
                valor = dados.get(campo_id, "")
                if valor:
                    try:
                        campo = self.page.locator(f"tr:has-text('{label}') input").first
                        campo.fill(str(valor))
                    except Exception:
                        pass

            # Passo 4: Outros Itens
            area = detectar_area(dados.get("classe", ""), dados.get("feito", ""))
            regras = obter_regras_outros_itens(area)

            for item in regras:
                self.page.select_option("select[name='itemGuia'], #itemGuia", item["item_guia"])
                self.page.wait_for_timeout(1000)
                self.page.wait_for_selector(f"input[value='{item['item_calculo']}']", timeout=5000)
                self.page.click(f"input[value='{item['item_calculo']}']")

                if item.get("usa_ids_oficios") and dados.get("ids_oficios"):
                    self.page.fill("input[name='numeroFolhasOutros'], #numeroFolhasOutros", dados["ids_oficios"])

                if item.get("usa_valor_causa_atualizado") and valor_causa_atualizado:
                    self.page.fill("input[name='valorItem'], #valorItem", valor_causa_atualizado)

                self.page.fill("input[name='quantidade'], #quantidade", str(item.get("quantidade", 1)))
                self.page.click("text='Adicionar'", timeout=5000)
                self.page.wait_for_timeout(500)

            # Passo 5: Custas Pagas
            for cp in dados.get("custas_pagas", []):
                data_pag = _formatar_data(cp.get("data", ""))
                self.page.fill("input[name='dataPagamento'], #dataPagamento", data_pag)
                self.page.fill("input[name='valorCustasPagas'], #valorCustasPagas", cp.get("valor", ""))
                self.page.fill("input[name='numeroGuia'], #numeroGuia", cp.get("numero_guia", ""))
                self.page.click("text='Adicionar'", timeout=5000)
                self.page.wait_for_timeout(500)

            # Passo 6: Avançar e capturar resultado
            self.page.click("text='Avançar'", timeout=10000)
            self.page.wait_for_timeout(3000)

            try:
                valor_total = self.page.locator("text=/Valor Total a Recolher/i >> xpath=following-sibling::*").inner_text(timeout=5000)
                resultado["valor_total_recolher"] = valor_total
            except Exception:
                try:
                    html = self.page.content()
                    m = re.search(r"Valor Total a Recolher[\s:]*R?\$?\s*([\d.,]+)", html, re.IGNORECASE)
                    if m:
                        resultado["valor_total_recolher"] = m.group(1)
                except Exception:
                    pass

            screenshot_path = SCREENSHOTS_DIR / f"{numero_processo}_sistjweb.png"
            self.page.screenshot(path=str(screenshot_path), full_page=True)
            resultado["screenshot_path"] = str(screenshot_path)

            self.page.click("text='Gravar'", timeout=10000)
            self.page.wait_for_timeout(2000)

            info(f"Planilha SISTJWEB preenchida para {numero_processo}.")
            return resultado
        except Exception as e:
            erro(f"Falha ao preencher SISTJWEB para {numero_processo}: {e}")
            raise

    def gravar_e_aprovar(self, numero_processo: str) -> str:
        """
        Navega até o processo salvo e clica 'Gravar e Aprovar'.
        Retorna caminho do PDF baixado.
        """
        try:
            self.page.goto(SISTJ_URL, wait_until="networkidle")
            self.page.click("text='Custas'", timeout=10000)
            self.page.click("text='Atualizar Planilha da Contadoria'", timeout=10000)
            self.page.click("text='Preencher'", timeout=10000)

            self.page.fill("input[name='numeroProcesso'], #numero", numero_processo)
            self.page.click("text='Consultar'", timeout=5000)
            self.page.wait_for_timeout(2000)

            self.page.click(f"text='{numero_processo}'", timeout=5000)
            self.page.wait_for_timeout(2000)

            with self.page.expect_download() as download_info:
                self.page.click("text='Gravar e Aprovar'", timeout=10000)
            download = download_info.value

            caminho_pdf = str(DEMONSTRATIVOS_DIR / f"{numero_processo}.pdf")
            download.save_as(caminho_pdf)

            info(f"Demonstrativo baixado: {caminho_pdf}")
            return caminho_pdf
        except Exception as e:
            erro(f"Falha ao gravar/aprovar no SISTJWEB: {e}")
            raise
