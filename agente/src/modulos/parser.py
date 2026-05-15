"""
Extração de dados a partir dos documentos do PJE.
Regex para sentenças, comprovantes de pagamento, etc.
"""
import re
from typing import List, Dict, Any


def extrair_ids(docs: List[Dict[str, Any]], tipo_doc: str) -> str:
    """Concatena IDs de um tipo de documento separados por vírgula sem espaço."""
    ids = [str(d["doc_id"]) for d in docs if d.get("tipo") == tipo_doc]
    return ",".join(ids)


def parse_sentenca(texto: str) -> Dict[str, Any]:
    """
    Extrai informações da sentença.
    """
    resultado = {
        "sucumbente_nome": "",
        "honorarios_percentual": "",
        "suspensao_exigibilidade": False,
        "valor_condenacao": "",
    }

    # Sucumbente
    m = re.search(
        r"condeno\s+(?:\w+\s+)?([A-ZÁÉÍÓÚÃÕÀÂÊÎÔÛÇ][A-ZÁÉÍÓÚÃÕÀÂÊÎÔÛÇa-záéíóúãõàâêîôûç\s\.]+?)\s+ao\s+pagamento",
        texto,
        re.IGNORECASE,
    )
    if m:
        resultado["sucumbente_nome"] = m.group(1).strip()

    # Honorários
    m = re.search(r"honorários[^%]+?(\d+(?:,\d+)?)\s*%", texto, re.IGNORECASE)
    if m:
        resultado["honorarios_percentual"] = m.group(1)

    # Suspensão de exigibilidade (art 98 § 3)
    if re.search(r"art(?:igo)?\.?\s*98.{0,50}§\s*3", texto, re.IGNORECASE | re.DOTALL):
        resultado["suspensao_exigibilidade"] = True

    # Valor da condenação
    m = re.search(
        r"valor\s+d[ae]\s+condena[çc][ãa]o\s+de\s+R\$\s*([\d.,]+)",
        texto,
        re.IGNORECASE,
    )
    if m:
        resultado["valor_condenacao"] = m.group(1)

    return resultado


def parse_comprovante_pagamento(texto: str) -> Dict[str, Any]:
    """Extrai data, valor e número da guia de comprovante de pagamento."""
    resultado = {"data": "", "valor": "", "numero_guia": ""}

    m = re.search(
        r"(?:data\s+d[eo]\s+pagamento|pago\s+em)[:\s]+(\d{2}/\d{2}/\d{4})",
        texto,
        re.IGNORECASE,
    )
    if m:
        resultado["data"] = m.group(1)

    m = re.search(
        r"(?:valor\s+(?:pago|das\s+custas\s+pagas)|valor\s+recolhido)[:\s]+R?\$?\s*([\d.,]+)",
        texto,
        re.IGNORECASE,
    )
    if m:
        resultado["valor"] = m.group(1)

    m = re.search(
        r"(?:guia\s+n[º°\.]+\s*|número\s+da\s+guia[:\s]+)(\d+)",
        texto,
        re.IGNORECASE,
    )
    if m:
        resultado["numero_guia"] = m.group(1)

    return resultado


def processar_documentos(docs: List[Dict[str, Any]], textos: Dict[str, str]) -> Dict[str, Any]:
    """
    Processa lista de documentos e seus textos.
    docs: lista de dicts com doc_id, tipo, data_assinatura, nome
    textos: dict mapeando doc_id -> texto extraído
    """
    resultado = {
        "ids_oficios": extrair_ids(docs, "Ofício"),
        "ids_alvaras": extrair_ids(docs, "Alvará"),
        "ids_traslados": extrair_ids(docs, "Traslado"),
        "ids_mandados": extrair_ids(docs, "Mandado"),
        "ids_cartas_sentenca": extrair_ids(docs, "Carta de Sentença"),
        "ids_ar": extrair_ids(docs, "AR"),
        "ids_armp": extrair_ids(docs, "AR/MP"),
        "ids_circunscricao_origem": extrair_ids(docs, "Diligência"),
        "ids_outra_circunscricao": "",
        "custas_pagas": [],
        "sucumbente_nome": "",
        "honorarios_percentual": "",
        "suspensao_exigibilidade": False,
    }

    for doc in docs:
        tipo = doc.get("tipo", "")
        doc_id = str(doc.get("doc_id", ""))
        texto = textos.get(doc_id, "")

        if tipo in ("Sentença", "Decisão"):
            info = parse_sentenca(texto)
            if info["sucumbente_nome"]:
                resultado["sucumbente_nome"] = info["sucumbente_nome"]
            if info["honorarios_percentual"]:
                resultado["honorarios_percentual"] = info["honorarios_percentual"]
            if info["suspensao_exigibilidade"]:
                resultado["suspensao_exigibilidade"] = True

        elif tipo == "Comprovante de Pagamento de Custas":
            info = parse_comprovante_pagamento(texto)
            if info["data"] or info["valor"] or info["numero_guia"]:
                resultado["custas_pagas"].append(info)

    return resultado
