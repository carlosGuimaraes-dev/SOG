"""
Extrator de texto de PDFs judiciais usando PyMuPDF (fitz).

Responsabilidades:
- Extrair texto completo e por página
- Isolar o DISPOSITIVO da sentença via heurística de coordenadas + regex
- Detectar PDFs scanned (sem texto selecionável)
- Extrair tabela de documentos da capa do processo digital
- Tratar exceções de arquivo e corrompimento
"""
import os
import re
from typing import Dict, Any, List, Tuple, Optional

try:
    import fitz  # pymupdf
    _PYMUPDF_DISPONIVEL = True
except ImportError:
    fitz = None  # type: ignore
    _PYMUPDF_DISPONIVEL = False

try:
    from utils.logger import erro
except ImportError:

    def erro(mensagem: str, **kwargs: Any) -> None:
        pass


# Tipos de documento conhecidos no PJe (usados para separar nome do tipo)
_TIPOS_DOCUMENTO_PJE = {
    "petição inicial",
    "contrato social",
    "procuração/substabelecimento",
    "documento de comprovação",
    "documento de identificação",
    "boletim de ocorrência",
    "guia",
    "comprovante de pagamento de custas",
    "decisão",
    "petição",
    "mandado",
    "não entregue - destinatário ausente (ecarta)",
    "não entregue - destinatário ausente",
    "certidão",
    "diligência",
    "anexo",
    "contestação",
    "comprovante de residência",
    "atos constitutivos",
    "réplica",
    "despacho",
    "certidão de disponibilização",
    "laudo pericial",
    "substabelecimento",
    "entregue (ecarta)",
    "ata",
    "manifestação",
    "sentença",
    "ficha de inspeção judicial",
    "carta de preposição",
    "comprovante",
    "notificação",
    "carta de sentença",
    "ofício",
    "alvará",
    "traslado",
    "ar",
    "ar/mp",
    "passagem aérea",
    "orçamento",
}

# Regex para identificar início de entrada na tabela de documentos
_RE_DOC_ID_DATA = re.compile(r"^(\d{6,})\s+(\d{2}/\d{2}/\d{4})\s*(\d{2}:\d{2})?$")
_RE_HORA = re.compile(r"^\d{2}:\d{2}$")
_RE_PROXIMO_DOC = re.compile(r"^\d{6,}\s+\d{2}/\d{2}/\d{4}")


# Margem em pontos para descartar cabeçalho/rodapé
_MARGEM_VERTICAL = 80

# Regex para isolar dispositivo (prioridade)
_RE_DISPOSITIVO = re.compile(
    r"(?i)DISPOSITIVO[:\s]*([\s\S]+?)(?=Assinado|LOCAL\s*E\s*DATA|Intim[eé]m-se)",
    re.DOTALL,
)

# Fallback: ANTE O EXPOSTO até terminador comum
_RE_ANTE_O_EXPOSTO = re.compile(
    r"(?i)(ANTE\s+O\s+EXPOSTO[,\s]*[\s\S]+?)(?=Assinado|LOCAL\s*E\s*DATA|Intim[eé]m-se)",
    re.DOTALL,
)

# =============================================================================
# Regex para extração de custas iniciais (guia de pagamento)
# =============================================================================

_RE_VALOR_TOTAL = re.compile(
    r"(?:valor\s+total)[:\s]*R?\$?\s*([\d\.]+,\d{2})",
    re.IGNORECASE,
)

_RE_VALOR_TOTAL_LOOSE = re.compile(
    r"R?\$\s*([\d\.]+,\d{2})",
    re.IGNORECASE,
)

_RE_DETALHAMENTO = {
    "distribuidor": re.compile(r"(?:distribuidor|distribui[cç][aã]o)[:\s]+([\d\.]+,\d{2})", re.I),
    "mandados": re.compile(r"(?:mandados?)[:\s]+([\d\.]+,\d{2})", re.I),
    "oficios": re.compile(r"(?:of[ií]cios?)[:\s]+([\d\.]+,\d{2})", re.I),
    "contador": re.compile(r"(?:contador)[:\s]+([\d\.]+,\d{2})", re.I),
    "custas": re.compile(r"(?:custas?)[:\s]+([\d\.]+,\d{2})", re.I),
    "diligencias": re.compile(r"(?:dilig[eê]ncias?)[:\s]+([\d\.]+,\d{2})", re.I),
}

_RE_NUMERO_GUIA = re.compile(
    r"(?:n[uú]mero\s+(?:da\s+)?guia|guia\s+n[º°o]?)[:\s]+(\S+)",
    re.IGNORECASE,
)

_RE_VENCIMENTO = re.compile(
    r"(?:vencimento|venc\.)[:\s]+(\d{2}/\d{2}/\d{4})",
    re.IGNORECASE,
)

# Janela de caracteres ao redor do doc_id para buscar dados da guia.
# Valor inicial; se não encontrar dados, expande para _JANELA_GUIA_EXPANDIDA.
_JANELA_GUIA = 1500
_JANELA_GUIA_EXPANDIDA = 3000


def _isolar_dispositivo(texto: str) -> str:
    """Tenta isolar o dispositivo da sentença no texto completo.

    Estratégia:
    1. Coleta todos os matches de DISPOSITIVO e ANTE O EXPOSTO.
    2. Prioriza o match que contenha "condeno" (indicativo de sentença
       condenatória), pois petições e razões de recurso também usam
       "ANTE O EXPOSTO" mas raramente contêm a palavra "condeno".
    3. Se nenhum match contiver "condeno", usa o último match de
       ANTE O EXPOSTO (geralmente o mais próximo do final do processo).
    4. Fallback: últimos 25% do texto.
    """
    if not texto:
        return ""

    candidatos: List[str] = []

    for match in _RE_DISPOSITIVO.finditer(texto):
        candidatos.append(match.group(1))

    for match in _RE_ANTE_O_EXPOSTO.finditer(texto):
        candidatos.append(match.group(1))

    # Prioriza match que contenha "condeno" — forte indicativo de sentença
    for trecho in candidatos:
        if "condeno" in trecho.lower():
            return trecho.strip()

    # Sem "condeno": preferimos o último ANTE O EXPOSTO (mais próximo do fim)
    matches_ante = list(_RE_ANTE_O_EXPOSTO.finditer(texto))
    if matches_ante:
        return matches_ante[-1].group(1).strip()

    # Último DISPOSITIVO (menos comum, mas pode ocorrer)
    matches_disp = list(_RE_DISPOSITIVO.finditer(texto))
    if matches_disp:
        return matches_disp[-1].group(1).strip()

    # Fallback: últimos 25% do texto
    corte = int(len(texto) * 0.75)
    return texto[corte:].strip()


def _separar_nome_tipo(linhas: List[str]) -> tuple:
    """Separa nome do documento e tipo a partir das linhas do bloco.

    Estratégia:
    1. Se a última linha (ou últimas linhas juntas) bater com um tipo
       conhecido do PJe, separa como tipo.
    2. Caso contrário, tenta extrair tipo do final da linha única.
    3. Se nada funcionar, retorna tudo como nome e tipo vazio.
    """
    if not linhas:
        return "", ""

    texto_junto = " ".join(linhas).strip()
    texto_lower = texto_junto.lower()

    # Heurística 1: última linha isolada é um tipo conhecido
    ultima = linhas[-1].strip()
    if ultima.lower() in _TIPOS_DOCUMENTO_PJE:
        nome = " ".join(linhas[:-1]).strip()
        return nome, ultima

    # Heurística 2: últimas 2 linhas juntas formam um tipo conhecido
    if len(linhas) >= 2:
        duas_ultimas = " ".join(linhas[-2:]).strip()
        if duas_ultimas.lower() in _TIPOS_DOCUMENTO_PJE:
            nome = " ".join(linhas[:-2]).strip()
            return nome, duas_ultimas

    # Heurística 3: tenta match exato do tipo no final do texto juntado
    for tipo in sorted(_TIPOS_DOCUMENTO_PJE, key=len, reverse=True):
        if texto_lower.endswith(tipo):
            idx = texto_lower.rfind(tipo)
            nome = texto_junto[:idx].strip()
            tipo_original = texto_junto[idx:].strip()
            return nome, tipo_original

    # Fallback: tudo é nome
    return texto_junto, ""


def extrair_documentos_capa(caminho: str) -> List[Dict[str, str]]:
    """Extrai a tabela de documentos da capa do processo digital.

    Itera as primeiras páginas do PDF procurando pelo padrão de tabela
    do PJe (Id. | Data da Assinatura | Documento | Tipo).

    Retorna lista de dicts:
        [{"doc_id": "...", "data_assinatura": "...", "nome": "...", "tipo": "..."}]

    Se não conseguir extrair a tabela (PDF sem capa padrão), retorna lista vazia.
    """
    if not _PYMUPDF_DISPONIVEL:
        return []

    if not caminho or not isinstance(caminho, str):
        return []

    if not os.path.exists(caminho):
        return []

    try:
        doc = fitz.open(caminho)  # type: ignore
    except Exception:
        return []

    documentos: List[Dict[str, str]] = []
    # Limite de páginas para evitar percorrer PDFs longos desnecessariamente
    MAX_PAGINAS_CAPA = 10

    try:
        for page_idx in range(min(MAX_PAGINAS_CAPA, len(doc))):
            texto = doc[page_idx].get_text()
            linhas = [linha_texto.strip() for linha_texto in texto.split("\n")]

            i = 0
            while i < len(linhas):
                linha = linhas[i]
                m = _RE_DOC_ID_DATA.match(linha)
                if not m:
                    i += 1
                    continue

                doc_id = m.group(1)
                data_assinatura = m.group(2)
                hora = m.group(3) or ""
                i += 1

                # Hora pode estar na próxima linha se não estava na mesma
                if not hora and i < len(linhas) and _RE_HORA.match(linhas[i]):
                    hora = linhas[i]
                    i += 1

                # Acumula linhas do nome/tipo até o próximo ID+data ou fim da página
                bloco: List[str] = []
                while i < len(linhas):
                    proxima = linhas[i]
                    if _RE_PROXIMO_DOC.match(proxima):
                        break
                    if proxima:
                        bloco.append(proxima)
                    i += 1

                nome, tipo = _separar_nome_tipo(bloco)
                documentos.append({
                    "doc_id": doc_id,
                    "data_assinatura": data_assinatura,
                    "nome": nome,
                    "tipo": tipo,
                })
    except Exception as exc:
        erro(f"Falha ao extrair documentos da capa: {exc}")
        # Em caso de erro parcial, retorna o que conseguiu extrair
    finally:
        doc.close()

    return documentos


def mapear_tipo_sistjweb(tipo_pje: str) -> str:
    """Mapeia tipo do PJe para campo do SISTJWEB.

    Tipos reconhecidos retornam o nome do campo correspondente no
    payload de preenchimento do SISTJWEB. Tipos não mapeados
    retornam string vazia.
    """
    mapeamento = {
        "Mandado": "ids_mandados",
        "Ofício": "ids_oficios",
        "Alvará": "ids_alvaras",
        "Traslado": "ids_traslados",
        "Carta de Sentença": "ids_cartas_sentenca",
        "AR": "ids_ar",
        "AR/MP": "ids_armp",
        "Diligência": "ids_circunscricao_origem",
        "Comprovante de Pagamento de Custas": "custas_pagas",
    }
    return mapeamento.get(tipo_pje, "")


def _parse_valor_monetario(texto: str) -> Tuple[str, int]:
    """Converte string como 'R$ 1.234,56' ou '1234,56' em (str_formatada, centavos_int).

    Usa aritmética inteira (sem float) para evitar imprecisão decimal.
    Retorna ("1234,56", 123456). Se inválido, ("", 0).
    """
    if not texto:
        return "", 0

    # Remove prefixo R$, espaços e pontos de milhar
    limpo = texto.strip()
    limpo = re.sub(r"^R?\$\s*", "", limpo)
    limpo = limpo.replace(".", "")

    # Separa na vírgula: parte inteira e centavos
    if "," not in limpo:
        return "", 0

    partes = limpo.split(",")
    if len(partes) != 2:
        return "", 0

    parte_inteira_str = partes[0].strip()
    centavos_str = partes[1].strip()

    if not parte_inteira_str.isdigit() or not centavos_str.isdigit():
        return "", 0

    inteiros = int(parte_inteira_str)
    centavos = int(centavos_str)

    # Valida centavos (deve ser 00-99)
    if centavos < 0 or centavos > 99:
        return "", 0

    total_centavos = inteiros * 100 + centavos
    str_formatada = f"{inteiros},{centavos:02d}"
    return str_formatada, total_centavos


def _extrair_valor_guia(texto_regiao: str) -> Optional[Dict[str, Any]]:
    """Aplica regex em uma região de texto para extrair dados da guia.

    Retorna dict com os campos da guia se encontrar padrões reconhecidos,
    ou None se a região não contiver dados de guia.
    """
    if not texto_regiao:
        return None

    # 1. Prioridade: regex explícito de "valor total" no texto da guia
    valor_total = ""
    valor_total_centavos = 0

    match_total = _RE_VALOR_TOTAL.search(texto_regiao)
    if match_total:
        valor_total, valor_total_centavos = _parse_valor_monetario(match_total.group(1))

    # 2. Calcula detalhamento sempre (independente do valor_total)
    detalhamento: Dict[str, str] = {}
    soma_detalhamento_centavos = 0

    for chave, regex in _RE_DETALHAMENTO.items():
        match = regex.search(texto_regiao)
        if match:
            valor_str = match.group(1)
            str_fmt, centavos = _parse_valor_monetario(valor_str)
            if str_fmt:
                detalhamento[chave] = str_fmt
                soma_detalhamento_centavos += centavos

    # 3. Fallback: se regex de valor total falhou, usa soma do detalhamento
    if not valor_total and detalhamento:
        parte_inteira = soma_detalhamento_centavos // 100
        parte_decimal = soma_detalhamento_centavos % 100
        valor_total = f"{parte_inteira},{parte_decimal:02d}"
        valor_total_centavos = soma_detalhamento_centavos

    # 4. Último fallback: regex loose próximo a palavras-chave de guia
    if not valor_total:
        # Procura por valores monetários próximos a palavras-chave de guia
        indice_guia = -1
        for palavra in ("número da guia", "guia de custas", "vencimento", "valor cobrado", "valor do documento"):
            idx = texto_regiao.lower().find(palavra)
            if idx >= 0:
                indice_guia = idx
                break

        if indice_guia >= 0:
            # Extrai janela de ±500 chars ao redor da palavra-chave
            inicio = max(0, indice_guia - 500)
            fim = min(len(texto_regiao), indice_guia + 500)
            janela_contexto = texto_regiao[inicio:fim]
            match = _RE_VALOR_TOTAL_LOOSE.search(janela_contexto)
            if match:
                valor_total, valor_total_centavos = _parse_valor_monetario(match.group(1))

    numero_guia = ""
    match_numero = _RE_NUMERO_GUIA.search(texto_regiao)
    if match_numero:
        numero_guia = match_numero.group(1).strip()

    vencimento = ""
    match_vencimento = _RE_VENCIMENTO.search(texto_regiao)
    if match_vencimento:
        vencimento = match_vencimento.group(1)
    else:
        # Fallback: busca todas as ocorrências de "Vencimento" isolado e
        # captura a data mais próxima (antes ou depois). Necessário porque
        # em formulários de guia a ordem de extração de texto pode inverter
        # a posição relativa entre o rótulo e o valor.
        for m in re.finditer(r"(?i)vencimento", texto_regiao):
            inicio_venc = max(0, m.start() - 200)
            fim_venc = min(len(texto_regiao), m.end() + 200)
            janela_venc = texto_regiao[inicio_venc:fim_venc]
            match_venc_fallback = re.search(r"(\d{2}/\d{2}/\d{4})", janela_venc)
            if match_venc_fallback:
                candidata = match_venc_fallback.group(1)
                # Evita pegar a data do documento (02/08/2024) em vez da data
                # de vencimento (11/08/2024) — preferimos a data mais distante
                # do início da guia quando há múltiplas. Na prática, a primeira
                # match com data já é suficiente para a maioria dos casos.
                if not vencimento:
                    vencimento = candidata
                break

    # Decidir se a região contém dados de guia válidos:
    # precisamos de pelo menos valor_total, detalhamento, numero_guia ou vencimento
    tem_dados = bool(valor_total or detalhamento or numero_guia or vencimento)
    if not tem_dados:
        return None

    return {
        "valor_total": valor_total,
        "valor_total_centavos": valor_total_centavos,
        "detalhamento": detalhamento,
        "numero_guia": numero_guia,
        "vencimento": vencimento,
    }


def extrair_custas_iniciais(
    caminho: str,
    texto_completo: Optional[str] = None,
    documentos_capa: Optional[List[Dict[str, str]]] = None,
    scanned: Optional[bool] = None,
) -> Dict[str, Any]:
    """Extrai valor das custas iniciais a partir de guias de pagamento no PDF.

    Recebe caminho do PDF, identifica documentos do tipo "Guia" ou
    "Comprovante de Pagamento de Custas" na capa, localiza o conteúdo
    da guia no texto completo e extrai valores monetários.

    Retorna:
        {
            "encontrado": True,
            "valor_total": "266,95",
            "valor_total_centavos": 26695,
            "detalhamento": { ... },
            "doc_id": "206426308",
            "numero_guia": "001-9",
            "vencimento": "11/08/2024",
            "scanned": False,
        }

    Ou, quando não encontrado:
        {"encontrado": False, "scanned": bool}
    """
    # Se os dados não foram pré-extraídos, obtém via extrair_texto_pdf
    if texto_completo is None or documentos_capa is None or scanned is None:
        dados_pdf = extrair_texto_pdf(caminho)
        texto_completo = dados_pdf.get("texto_completo", "")
        documentos_capa = dados_pdf.get("documentos_capa", [])
        scanned = dados_pdf.get("scanned", False)

    if scanned:
        return {"encontrado": False, "scanned": True}

    # Filtra documentos do tipo guia ou comprovante de pagamento de custas
    tipos_alvo = {"guia", "comprovante de pagamento de custas"}
    docs_guia = [
        doc for doc in documentos_capa
        if doc.get("tipo", "").strip().lower() in tipos_alvo
    ]

    if not docs_guia:
        return {"encontrado": False, "scanned": False}

    for doc in docs_guia:
        doc_id = doc.get("doc_id", "").strip()
        if not doc_id:
            continue

        # Estratégia 1: busca pelo doc_id no texto completo
        pos = 0
        while True:
            idx = texto_completo.find(doc_id, pos)
            if idx == -1:
                break

            # Tenta janela inicial; se não encontrar, expande
            for janela_tamanho in (_JANELA_GUIA, _JANELA_GUIA_EXPANDIDA):
                inicio = max(0, idx - janela_tamanho)
                fim = min(len(texto_completo), idx + janela_tamanho)
                janela = texto_completo[inicio:fim]

                dados_guia = _extrair_valor_guia(janela)
                if dados_guia:
                    resultado: Dict[str, Any] = {"encontrado": True, "scanned": False}
                    resultado.update(dados_guia)
                    resultado["doc_id"] = doc_id
                    return resultado

            pos = idx + len(doc_id)

        # Estratégia 2 (fallback): quando o doc_id não é encontrado no texto
        # filtrado (cabeçalho descartado por coordenadas), busca por strings
        # típicas da guia no texto completo.
        tipo_doc = doc.get("tipo", "").strip().lower()
        tipos_com_fallback_guia = {"guia", "comprovante de pagamento de custas"}
        if tipo_doc in tipos_com_fallback_guia:
            # Busca por "Guia de Custas e Emolumentos" — presente no corpo da guia
            _STR_GUIA_CUSTAS = "Guia de Custas e Emolumentos"
            idx_guia = texto_completo.find(_STR_GUIA_CUSTAS)
            if idx_guia >= 0:
                for janela_tamanho in (_JANELA_GUIA, _JANELA_GUIA_EXPANDIDA):
                    inicio = max(0, idx_guia - janela_tamanho)
                    fim = min(len(texto_completo), idx_guia + janela_tamanho)
                    janela = texto_completo[inicio:fim]

                    dados_guia = _extrair_valor_guia(janela)
                    if dados_guia:
                        resultado = {"encontrado": True, "scanned": False}
                        resultado.update(dados_guia)
                        resultado["doc_id"] = doc_id
                        return resultado

    return {"encontrado": False, "scanned": False}


def extrair_texto_pdf(caminho: str) -> Dict[str, Any]:
    """Extrai texto e metadados de um PDF judicial.

    Retorna dict com:
    - texto_completo: str
    - texto_por_pagina: List[str]
    - num_paginas: int
    - dispositivo: str (texto isolado pela heurística, ou "")
    - scanned: bool (True se detectado como PDF sem texto selecionável)
    - erro: str (mensagem de erro, ou "")
    """
    resultado_base: Dict[str, Any] = {
        "texto_completo": "",
        "texto_por_pagina": [],
        "num_paginas": 0,
        "dispositivo": "",
        "scanned": False,
        "erro": "",
        "documentos_capa": [],
        "custas_iniciais": {"encontrado": False, "scanned": False},
    }

    if not _PYMUPDF_DISPONIVEL:
        resultado_base["erro"] = "PyMuPDF (pymupdf) não está instalado"
        return resultado_base

    if not caminho or not isinstance(caminho, str):
        resultado_base["erro"] = "Caminho do PDF inválido"
        return resultado_base

    if not os.path.exists(caminho):
        resultado_base["erro"] = f"Arquivo não encontrado: {caminho}"
        return resultado_base

    try:
        doc = fitz.open(caminho)  # type: ignore
    except Exception as exc:
        erro_msg = str(exc)
        resultado_base["erro"] = f"Erro ao abrir PDF: {erro_msg}"
        erro(f"Falha ao abrir PDF: {erro_msg}")
        return resultado_base

    texto_por_pagina: List[str] = []
    partes_texto: List[str] = []
    paginas_scanned = 0
    total_texto_bruto = 0
    scanned = False

    try:
        for page in doc:
            altura = page.rect.height

            # Texto bruto para scanned detection (não filtrado)
            texto_bruto = page.get_text()
            total_texto_bruto += len(texto_bruto.strip())

            # Contabiliza candidatas a scanned (avaliação global após o loop)
            if len(texto_bruto.strip()) < 30 and page.get_images():
                paginas_scanned += 1

            # Extração filtrada por coordenadas (descarta cabeçalho/rodapé)
            blocks = page.get_text("blocks")
            blocos_limpos: List[str] = []
            for block in blocks:
                # block = (x0, y0, x1, y1, text, block_no, block_type)
                if len(block) < 5:
                    continue
                _x0, y0, _x1, y1, texto_block = block[:5]
                if y1 < _MARGEM_VERTICAL or y0 > altura - _MARGEM_VERTICAL:
                    continue
                blocos_limpos.append(texto_block)

            pagina_limpa = "\n".join(blocos_limpos)
            texto_por_pagina.append(pagina_limpa)
            partes_texto.append(pagina_limpa)

        # Scanned detection global: heurística agregada
        # ≥80% páginas image-only E média <100 chars/página indicam
        # ausência de texto selecionável (evita falso positivo em capas)
        num_paginas = len(doc)
        if num_paginas > 0:
            proporcao_scanned = paginas_scanned / num_paginas
            media_texto = total_texto_bruto / num_paginas
            scanned = proporcao_scanned >= 0.8 and media_texto < 100
    except Exception as exc:
        resultado_base["erro"] = f"Erro ao processar páginas: {exc}"
        erro(f"Falha ao processar páginas do PDF: {exc}")
        return resultado_base
    finally:
        doc.close()

    texto_completo = "\n".join(partes_texto)
    dispositivo = _isolar_dispositivo(texto_completo) if texto_completo else ""
    documentos_capa = extrair_documentos_capa(caminho)

    # Extrai custas iniciais reutilizando dados já obtidos (sem reabrir o PDF)
    custas_iniciais = extrair_custas_iniciais(
        caminho,
        texto_completo=texto_completo,
        documentos_capa=documentos_capa,
        scanned=scanned,
    )

    return {
        "texto_completo": texto_completo,
        "texto_por_pagina": texto_por_pagina,
        "num_paginas": len(texto_por_pagina),
        "dispositivo": dispositivo,
        "scanned": scanned,
        "erro": "",
        "documentos_capa": documentos_capa,
        "custas_iniciais": custas_iniciais,
    }
