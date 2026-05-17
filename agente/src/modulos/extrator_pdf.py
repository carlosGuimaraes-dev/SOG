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
from typing import Dict, Any, List

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
            linhas = [l.strip() for l in texto.split("\n")]

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
    scanned = False

    try:
        for page in doc:
            altura = page.rect.height

            # Texto bruto para scanned detection (não filtrado)
            texto_bruto = page.get_text()

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

            # Scanned detection: pouco texto selecionável + presença de imagens
            if len(texto_bruto.strip()) < 30 and page.get_images():
                scanned = True
    except Exception as exc:
        resultado_base["erro"] = f"Erro ao processar páginas: {exc}"
        erro(f"Falha ao processar páginas do PDF: {exc}")
        doc.close()
        return resultado_base
    finally:
        doc.close()

    texto_completo = "\n".join(partes_texto)
    dispositivo = _isolar_dispositivo(texto_completo) if texto_completo else ""
    documentos_capa = extrair_documentos_capa(caminho)

    return {
        "texto_completo": texto_completo,
        "texto_por_pagina": texto_por_pagina,
        "num_paginas": len(texto_por_pagina),
        "dispositivo": dispositivo,
        "scanned": scanned,
        "erro": "",
        "documentos_capa": documentos_capa,
    }
