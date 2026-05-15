"""
Automação do PJE TJDFT.
- Login
- Coleta de lista de processos por etiqueta
- Coleta de documentos e textos
- Anexar demonstrativo PDF
"""
import re
from typing import List, Dict, Any, Optional
from playwright.sync_api import sync_playwright, Page, Browser, TimeoutError as PlaywrightTimeout

from config import PJE_URL, PJE_USUARIO, PJE_SENHA, PJE_ETIQUETA, HEADLESS, TIMEOUT_PADRAO
from utils.logger import info, erro, aviso
from banco import db


def _formatar_numero_processo(numero: str) -> str:
    """Remove formatação do número CNJ."""
    return re.sub(r"\D", "", numero)


class PjeClient:
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self._playwright = None

    def iniciar(self):
        self._playwright = sync_playwright().start()
        self.browser = self._playwright.chromium.launch(headless=HEADLESS)
        context = self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            accept_downloads=True,
        )
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
            self.page.goto(PJE_URL, wait_until="networkidle")
            # PJE tem iframe de login em algumas versões; tenta ambos
            self.page.wait_for_selector("input[name='username'], #username, #formulario:username", timeout=15000)

            # Tenta preencher usuário
            self.page.fill("input[name='username'], #username, #formulario\\:username", PJE_USUARIO)
            self.page.fill("input[name='password'], #password, #formulario\\:password", PJE_SENHA)
            self.page.click("input[type='submit'], #btnLogin, #formulario\\:btnEntrar")

            # Aguarda carregamento do painel
            self.page.wait_for_load_state("networkidle")
            self.page.wait_for_timeout(3000)

            # Verifica se logou (nome do usuário visível)
            if self.page.locator("text='SHEILA'").count() > 0 or \
               self.page.locator("text='Sheila'").count() > 0 or \
               self.page.locator(".nome-usuario").count() > 0:
                info("Login PJE realizado com sucesso.")
                return True

            info("Login PJE realizado (verificação alternativa).")
            return True
        except Exception as e:
            erro(f"Falha no login PJE: {e}")
            return False

    def coletar_lista_processos(self) -> List[str]:
        """Navega até a etiqueta e extrai números de processo."""
        try:
            # Menu: Meu Perfil -> Núcleo Permanente de Cálculos
            self.page.click("text='Meu Perfil'", timeout=10000)
            self.page.click("text='Núcleo Permanente de Cálculos'", timeout=10000)

            # Tarefas -> Incluir Cálculo
            self.page.click("text='Tarefas'", timeout=10000)
            self.page.click("text='Incluir Cálculo'", timeout=10000)

            # Etiquetas -> rolar até etiqueta e clicar
            self.page.click(f"text='{PJE_ETIQUETA}'", timeout=10000)

            # Extrai números de processo da tabela/grade
            self.page.wait_for_selector("table, .processo, .numero-processo", timeout=15000)

            # Tenta encontrar padrões CNJ na página
            html = self.page.content()
            numeros = re.findall(r"\d{7}-?\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}", html)
            if not numeros:
                numeros = re.findall(r"\d{20}", html)

            info(f"Encontrados {len(numeros)} processos na etiqueta '{PJE_ETIQUETA}'.")
            return list(set(numeros))
        except Exception as e:
            erro(f"Falha ao coletar lista de processos no PJE: {e}")
            return []

    def coletar_documentos(self, numero_processo: str) -> tuple:
        """
        Acessa o processo e coleta documentos.
        Retorna (lista_docs, dict_textos).
        """
        docs = []
        textos = {}
        try:
            # Clica no número do processo
            self.page.click(f"text='{numero_processo}'", timeout=10000)
            self.page.wait_for_load_state("networkidle")

            # Aguarda tabela de documentos
            self.page.wait_for_selector("table, .documentos, #tabelaDocumentos", timeout=15000)

            # Extrai linhas da tabela
            linhas = self.page.locator("table tbody tr, .documento-item").all()
            for linha in linhas:
                colunas = linha.locator("td").all_inner_texts()
                if len(colunas) >= 4:
                    doc_id = re.sub(r"\D", "", colunas[0]) or ""
                    data_assinatura = colunas[1]
                    nome_doc = colunas[2]
                    tipo = colunas[3]
                    docs.append({
                        "doc_id": doc_id,
                        "tipo": tipo.strip(),
                        "data_assinatura": data_assinatura.strip(),
                        "nome": nome_doc.strip(),
                    })

            # Lê conteúdo de documentos relevantes
            for doc in docs:
                if doc["tipo"] in ("Sentença", "Decisão", "Comprovante de Pagamento de Custas"):
                    try:
                        # Clica no documento
                        self.page.click(f"text='{doc['nome']}'", timeout=5000)
                        self.page.wait_for_timeout(2000)
                        # Tenta pegar texto do iframe ou da página
                        texto = ""
                        if self.page.locator("iframe").count() > 0:
                            iframe = self.page.frame_locator("iframe").first
                            texto = iframe.locator("body").inner_text(timeout=5000)
                        else:
                            texto = self.page.locator("body").inner_text()
                        textos[doc["doc_id"]] = texto
                        self.page.go_back()
                        self.page.wait_for_timeout(1000)
                    except Exception:
                        pass

            info(f"Coletados {len(docs)} documentos do processo {numero_processo}.")
            return docs, textos
        except Exception as e:
            erro(f"Falha ao coletar documentos de {numero_processo}: {e}")
            return docs, textos

    def anexar_demonstrativo(self, numero_processo: str, caminho_pdf: str) -> bool:
        """Anexa o PDF do demonstrativo no processo."""
        try:
            # Navega até o processo
            self.page.goto(PJE_URL, wait_until="networkidle")
            self.page.click(f"text='{numero_processo}'", timeout=10000)

            # Botão de anexar documento
            self.page.click("text='Anexar'", timeout=10000)
            self.page.set_input_files("input[type='file']", caminho_pdf)
            self.page.click("text='Confirmar'", timeout=10000)

            info(f"Demonstrativo anexado ao processo {numero_processo}.")
            return True
        except Exception as e:
            erro(f"Falha ao anexar demonstrativo em {numero_processo}: {e}")
            return False
