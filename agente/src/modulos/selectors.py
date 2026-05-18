"""
Constantes de seletores CSS para automação do SISTJWEB (TJDFT).

Cada constante é uma lista de seletores onde o primeiro elemento é o
seletor primário e os demais são fallbacks. Isso permite tentativa
progressiva quando o DOM varia entre versões do sistema JSF.

Convenções de nomenclatura:
  - NAV_*    : itens de navegação (menus, submenus)
  - RADIO_*  : radio buttons
  - INPUT_*  : campos de texto/input
  - SELECT_* : dropdowns/selects
  - CHECK_*  : checkboxes
  - BTN_*    : botões de ação
  - TABLE_*  : tabelas/linhas de dados
  - LABEL_*  : labels ou textos de resultado

Templates dinâmicos (valores que vêm de dados de processo) são expostos
como funções geradoras para garantir escaping CSS antes da interpolação.
"""

from modulos.css_escape import escape_for_css

# ─────────────────────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────────────────────
LOGIN_USER = ["input[name='j_username']", "#username", "input[id*='username']"]
LOGIN_PASS = ["input[name='j_password']", "#password", "input[id*='password']", "input[type='password']"]
LOGIN_SUBMIT = ["input[type='submit']", "#btnLogin", "button[type='submit']"]

# ─────────────────────────────────────────────────────────────
# NAVEGAÇÃO PRINCIPAL (menus laterais/superiores)
# ─────────────────────────────────────────────────────────────
NAV_MENU_CUSTAS = ["text=Custas", "a:has-text('Custas')", "[id*='custas']", "span:has-text('Custas')"]
NAV_SUBMENU_ATUALIZAR = [
    "text=Atualizar Planilha da Contadoria",
    "a:has-text('Atualizar Planilha')",
    "a:has-text('Atualizar Planilha da Contadoria')",
]
NAV_BOTAO_PREENCHER = [
    "text=Preencher",
    "input[value='Preencher']",
    "button:has-text('Preencher')",
    "a:has-text('Preencher')",
]

# ─────────────────────────────────────────────────────────────
# PASSO 1 — DADOS DO PROCESSO
# ─────────────────────────────────────────────────────────────

# Processo eletrônico: radio "Sim"
RADIO_PROC_ELETRONICO_SIM = [
    "input[value='Sim'][name*='processoEletronico']",
    "#processoEletronicoSim",
    "input[type='radio'][value='Sim'][name*='eletronico']",
]

# Instância judicial
RADIO_INSTANCIA_1 = [
    "input[value='1'][name*='instancia']",
    "#instancia1",
    "input[type='radio'][value='1'][name*='instancia']",
]
RADIO_INSTANCIA_2 = [
    "input[value='2'][name*='instancia']",
    "#instancia2",
    "input[type='radio'][value='2'][name*='instancia']",
]

# Número do processo + botão Consultar
INPUT_NUMERO_PROCESSO = [
    "input[name='numeroProcesso']",
    "#numeroProcesso",
    "#numero",
    "input[id*='numeroProcesso']",
]
BTN_CONSULTAR = [
    "input[value='Consultar']",
    "button:has-text('Consultar')",
    "input[type='button'][value*='Consultar']",
    "input[type='submit'][value*='Consultar']",
]

# Campos de resultado/leitura da consulta
INPUT_VALOR_CAUSA_ATUALIZADO = [
    "input[name='valorCausaAtualizado']",
    "#valorCausaAtualizado",
    "input[id*='valorCausaAtualizado']",
]

# Campos de preenchimento
INPUT_VALOR_CAUSA = [
    "input[name='valorCausa']",
    "#valorCausa",
    "input[id*='valorCausa']",
]
INPUT_DATA_DISTRIBUICAO = [
    "input[name='dataDistribuicao']",
    "#dataDistribuicao",
    "input[id*='dataDistribuicao']",
]
INPUT_POLO_ATIVO = [
    "input[name='poloAtivo']",
    "#poloAtivo",
    "input[id*='poloAtivo']",
]
INPUT_POLO_PASSIVO = [
    "input[name='poloPassivo']",
    "#poloPassivo",
    "input[id*='poloPassivo']",
]

# ─────────────────────────────────────────────────────────────
# PASSO 2 — CUSTAS / GUIA / PARTES
# ─────────────────────────────────────────────────────────────
SELECT_TIPO_GUIA = [
    "select[name='tipoGuia']",
    "#tipoGuia",
    "select[id*='tipoGuia']",
]
CHECK_PRO_RATA = [
    "input[name='proRata']",
    "#proRata",
    "input[type='checkbox'][name*='proRata']",
    "input[id*='proRata']",
]

# Botão para adicionar autor (usado quando há múltiplos autores/sucumbentes)
BTN_ADICIONAR_AUTOR = [
    "input[value='Adicionar autor(es)']",
    "button:has-text('Adicionar autor(es)')",
    "input[type='button'][value*='Adicionar autor']",
]

# Campos do formulário de parte (modal ou inline)
INPUT_NOME_PARTE = [
    "input[name='nomeParte']",
    "#nomeParte",
    "input[id*='nomeParte']",
]
INPUT_CPF_CNPJ = [
    "input[name='cpfCnpj']",
    "#cpfCnpj",
    "input[id*='cpfCnpj']",
]
SELECT_TIPO_PARTE = [
    "select[name='tipoParte']",
    "#tipoParte",
    "select[id*='tipoParte']",
]
CHECK_ISENCAO_CUSTAS = [
    "input[name='isencaoCustas']",
    "#isencaoCustas",
    "input[type='checkbox'][name*='isencao']",
]

# ─────────────────────────────────────────────────────────────
# PASSO 3 — PEÇAS PROCESSUAIS (tabela dinâmica)
# ─────────────────────────────────────────────────────────────
# As peças ficam em uma tabela onde cada linha contém o label e um input.
# O seletor primário usa :has-text para localizar a linha (tr) e depois o input.
# Fallbacks usam id ou name quando previsíveis.

TABLE_PECAS_OFICIOS = [
    "tr:has-text('Ofícios') input",
    "input[name*='oficios']",
    "#oficios",
]
TABLE_PECAS_ALVARAS = [
    "tr:has-text('Alvarás') input",
    "input[name*='alvaras']",
    "#alvaras",
]
TABLE_PECAS_TRASLADOS = [
    "tr:has-text('Traslados') input",
    "input[name*='traslados']",
    "#traslados",
]
TABLE_PECAS_MANDADOS = [
    "tr:has-text('Mandados') input",
    "input[name*='mandados']",
    "#mandados",
]
TABLE_PECAS_CARTAS_SENTENCA = [
    "tr:has-text('Cartas de Sentença') input",
    "input[name*='cartasSentenca']",
    "#cartasSentenca",
]
TABLE_PECAS_AR = [
    "tr:has-text('AR') input",
    "input[name*='ar']",
    "#ar",
]
TABLE_PECAS_ARMP = [
    "tr:has-text('AR/MP') input",
    "input[name*='armp']",
    "#armp",
]
TABLE_PECAS_CIRCUNSCRICAO_ORIGEM = [
    "tr:has-text('Circunscrição de Origem') input",
    "input[name*='circunscricaoOrigem']",
    "#circunscricaoOrigem",
]
TABLE_PECAS_OUTRA_CIRCUNSCRICAO = [
    "tr:has-text('Outra Circunscrição') input",
    "input[name*='outraCircunscricao']",
    "#outraCircunscricao",
]

MAPEAMENTO_PECAS = {
    "ids_oficios": TABLE_PECAS_OFICIOS,
    "ids_alvaras": TABLE_PECAS_ALVARAS,
    "ids_traslados": TABLE_PECAS_TRASLADOS,
    "ids_mandados": TABLE_PECAS_MANDADOS,
    "ids_cartas_sentenca": TABLE_PECAS_CARTAS_SENTENCA,
    "ids_ar": TABLE_PECAS_AR,
    "ids_armp": TABLE_PECAS_ARMP,
    "ids_circunscricao_origem": TABLE_PECAS_CIRCUNSCRICAO_ORIGEM,
    "ids_outra_circunscricao": TABLE_PECAS_OUTRA_CIRCUNSCRICAO,
}

# ─────────────────────────────────────────────────────────────
# PASSO 4 — OUTROS ITENS
# ─────────────────────────────────────────────────────────────
SELECT_ITEM_GUIA = [
    "select[name='itemGuia']",
    "#itemGuia",
    "select[id*='itemGuia']",
]
# Radio de item de cálculo: o valor vem dinamicamente do backend (ex: "item1", "item2"...)
# Usar f-string com escape explícito no código consumidor (sistjweb.py).
# Removido template com placeholder para evitar interpolação acidental sem escaping.

INPUT_NUMERO_FOLHAS_OUTROS = [
    "input[name='numeroFolhasOutros']",
    "#numeroFolhasOutros",
    "input[id*='numeroFolhasOutros']",
]
INPUT_VALOR_ITEM = [
    "input[name='valorItem']",
    "#valorItem",
    "input[id*='valorItem']",
]
INPUT_QUANTIDADE = [
    "input[name='quantidade']",
    "#quantidade",
    "input[id*='quantidade']",
]

# ─────────────────────────────────────────────────────────────
# PASSO 5 — CUSTAS PAGAS
# ─────────────────────────────────────────────────────────────
INPUT_DATA_PAGAMENTO = [
    "input[name='dataPagamento']",
    "#dataPagamento",
    "input[id*='dataPagamento']",
]
INPUT_VALOR_CUSTAS_PAGAS = [
    "input[name='valorCustasPagas']",
    "#valorCustasPagas",
    "input[id*='valorCustasPagas']",
]
INPUT_NUMERO_GUIA = [
    "input[name='numeroGuia']",
    "#numeroGuia",
    "input[id*='numeroGuia']",
]

# ─────────────────────────────────────────────────────────────
# BOTÕES DE AÇÃO GENÉRICOS
# ─────────────────────────────────────────────────────────────
BTN_ADICIONAR = [
    "input[value='Adicionar']",
    "button:has-text('Adicionar')",
    "input[type='button'][value='Adicionar']",
]
BTN_AVANCAR = [
    "input[value='Avançar']",
    "button:has-text('Avançar')",
    "input[type='button'][value='Avançar']",
]
BTN_GRAVAR = [
    "input[value='Gravar']",
    "button:has-text('Gravar')",
    "input[type='button'][value='Gravar']",
]
BTN_GRAVAR_APROVAR = [
    "input[value='Gravar e Aprovar']",
    "button:has-text('Gravar e Aprovar')",
    "input[type='button'][value*='Gravar e Aprovar']",
]

# ─────────────────────────────────────────────────────────────
# RESULTADO / RESUMO
# ─────────────────────────────────────────────────────────────
LABEL_VALOR_TOTAL_RECOLHER = [
    "text=/Valor Total a Recolher/i",
    "label:has-text('Valor Total a Recolher')",
    "span:has-text('Valor Total a Recolher')",
    "div:has-text('Valor Total a Recolher')",
]

# Seletor para obter o elemento irmão/imediatamente após o label de valor total
VALOR_TOTAL_RECOLHER_SIBLING = [
    "text=/Valor Total a Recolher/i >> xpath=following-sibling::*",
    "text=/Valor Total a Recolher/i >> xpath=../following-sibling::*",
]

# ═══════════════════════════════════════════════════════════════
# SEÇÃO PJE TJDFT — Seletores específicos do Processo Judicial Eletrônico
# ═══════════════════════════════════════════════════════════════
#
# O PJE utiliza componentes RichFaces (JSF) que geram classes CSS
# previsíveis (.rich-table, .rich-table-row, .rich-table-cell).
# Os seletores abaixo cobrem login, menus, tabelas de processos,
# tabelas de documentos e visualização/anexação.

# ─────────────────────────────────────────────────────────────
# PJE — LOGIN (incluindo iframe)
# ─────────────────────────────────────────────────────────────
PJE_LOGIN_IFRAME = [
    "iframe[id*='login']",
    "iframe[name*='login']",
    "iframe[src*='login']",
    "iframe[src*='autentica']",
    "iframe",  # fallback: primeiro iframe da página
]
PJE_LOGIN_USER = [
    "input[name='username']",
    "#username",
    "input[id*='username']",
    "#formulario\\:username",
    "input[name*='j_username']",
]
PJE_LOGIN_PASS = [
    "input[name='password']",
    "#password",
    "input[id*='password']",
    "#formulario\\:password",
    "input[name*='j_password']",
    "input[type='password']",
]
PJE_LOGIN_SUBMIT = [
    "input[type='submit']",
    "#btnLogin",
    "button[type='submit']",
    "#formulario\\:btnEntrar",
    "input[value*='Entrar']",
    "input[value*='Login']",
]

# Indicadores de sucesso após login
PJE_LOGIN_SUCESSO = [
    ".nome-usuario",
    ".usuario-logado",
    "[class*='menu-lateral']",
    "#menuPrincipal",
    "a:has-text('Sair')",
    "a:has-text('Logout')",
]

# ─────────────────────────────────────────────────────────────
# PJE — NAVEGAÇÃO / MENUS
# ─────────────────────────────────────────────────────────────
PJE_NAV_MENU_PERFIL = [
    "text='Meu Perfil'",
    "a:has-text('Meu Perfil')",
    "span:has-text('Meu Perfil')",
    "li:has-text('Meu Perfil') >> a",
    "[class*='menu']:has-text('Meu Perfil')",
]
PJE_NAV_MENU_NUCLEO = [
    "text='Núcleo Permanente de Cálculos'",
    "a:has-text('Núcleo Permanente de Cálculos')",
    "span:has-text('Núcleo Permanente de Cálculos')",
]
PJE_NAV_MENU_TAREFAS = [
    "text='Tarefas'",
    "a:has-text('Tarefas')",
    "span:has-text('Tarefas')",
    "li:has-text('Tarefas') >> a",
]
PJE_NAV_SUBMENU_INCLUIR_CALCULO = [
    "text='Incluir Cálculo'",
    "a:has-text('Incluir Cálculo')",
    "span:has-text('Incluir Cálculo')",
]

# Etiqueta de processo (texto dinâmico — usar função geradora)
def pje_etiqueta_link(etiqueta: str):
    """Retorna lista de seletores para localizar link de etiqueta no PJe."""
    e = escape_for_css(etiqueta)
    return [
        f"text='{e}'",
        f"a:has-text('{e}')",
        f"span:has-text('{e}')",
        f"li:has-text('{e}') >> a",
    ]

# ─────────────────────────────────────────────────────────────
# PJE — TABELAS (processos e documentos)
# ─────────────────────────────────────────────────────────────
PJE_TABELA_PROCESSOS = [
    ".rich-table",               # container RichFaces
    "table.rich-table",
    ".processo",
    ".numero-processo",
    "table[class*='processo']",
    "tbody tr",                  # fallback genérico
]
PJE_TABELA_DOCUMENTOS = [
    ".rich-table",               # tabela de documentos também usa rich-table
    "table.rich-table",
    ".documentos",
    "#tabelaDocumentos",
    "table[id*='documento']",
    "table",
]
PJE_TABELA_LINHA = [
    ".rich-table-row",
    "table tbody tr",
    ".documento-item",
]
PJE_TABELA_CELULA = [
    ".rich-table-cell",
    "td",
]

# ─────────────────────────────────────────────────────────────
# PJE — PROCESSO (links com número CNJ)
# ─────────────────────────────────────────────────────────────
def pje_link_processo(numero: str):
    """Retorna lista de seletores para localizar link de processo no PJe."""
    n = escape_for_css(numero)
    return [
        f"a:has-text('{n}')",
        f"td:has-text('{n}')",
        f"span:has-text('{n}')",
        f"text='{n}'",
    ]

# ─────────────────────────────────────────────────────────────
# PJE — VISUALIZADOR DE DOCUMENTOS
# ─────────────────────────────────────────────────────────────
PJE_DOC_VISUALIZADOR_IFRAME = [
    "iframe[id*='visualiz']",
    "iframe[name*='visualiz']",
    "iframe[id*='doc']",
    "iframe[src*='visualiz']",
    "iframe",
]
PJE_DOC_VISUALIZADOR_MODAL = [
    ".modal-body",
    "[role='dialog']",
    "#visualizadorDocumento",
    "[class*='visualizador']",
]
def pje_doc_link_nome(nome: str):
    """Retorna lista de seletores para localizar link de documento no PJe."""
    n = escape_for_css(nome)
    return [
        f"text='{n}'",
        f"a:has-text('{n}')",
        f"span:has-text('{n}')",
        f"td:has-text('{n}')",
    ]

# ─────────────────────────────────────────────────────────────
# PJE — ANEXAR DOCUMENTO
# ─────────────────────────────────────────────────────────────
PJE_BTN_ANEXAR = [
    "text='Anexar'",
    "a:has-text('Anexar')",
    "button:has-text('Anexar')",
    "text='Anexar Documento'",
    "a:has-text('Anexar Documento')",
    "input[value*='Anexar']",
]
PJE_INPUT_FILE = [
    "input[type='file']",
    "input[id*='arquivo']",
    "input[name*='arquivo']",
    "input[id*='file']",
    "input[name*='file']",
]
PJE_BTN_CONFIRMAR_UPLOAD = [
    "text='Confirmar'",
    "button:has-text('Confirmar')",
    "input[value='Confirmar']",
    "text='Enviar'",
    "button:has-text('Enviar')",
    "input[value='Enviar']",
    "text='Salvar'",
    "button:has-text('Salvar')",
]
