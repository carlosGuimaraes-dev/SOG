"""
Orquestração de extração de dados a partir dos documentos do PJE.

As funções de parsing propriamente ditas foram movidas para extrator_sentenca.py.
Este módulo mantém wrappers para compatibilidade temporária e a função
processar_documentos que orquestra a extração.
"""
from typing import List, Dict, Any, Optional

from modulos.extrator_sentenca import extrair_sentenca_regex, parse_comprovante_pagamento


def extrair_ids(docs: List[Dict[str, Any]], tipo_doc: str) -> str:
    """Concatena IDs de um tipo de documento separados por vírgula sem espaço."""
    ids = [str(d["doc_id"]) for d in docs if d.get("tipo") == tipo_doc]
    return ",".join(ids)


def parse_sentenca(texto: str) -> Dict[str, Any]:
    """
    Extrai informações da sentença.

    .. deprecated::
        Use extrator_sentenca.extrair_sentenca_regex() diretamente.
        Mantido para compatibilidade temporária.
    """
    resultado_regex = extrair_sentenca_regex(texto, area="civel")
    return {
        "sucumbente_nome": resultado_regex.get("sucumbente_nome", ""),
        "honorarios_percentual": resultado_regex.get("honorarios_percentual", ""),
        "suspensao_exigibilidade": resultado_regex.get("suspensao_exigibilidade", False),
        "valor_condenacao": resultado_regex.get("valor_condenacao", ""),
    }


def processar_documentos(
    docs: List[Dict[str, Any]],
    textos: Dict[str, str],
    custas_iniciais: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Processa lista de documentos e seus textos.
    docs: lista de dicts com doc_id, tipo, data_assinatura, nome
    textos: dict mapeando doc_id -> texto extraído
    custas_iniciais: lista de dicts {data, valor, numero_guia} extraídos de PDFs
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

    # Mescla custas extraídas de PDFs (sem duplicar por numero_guia)
    if custas_iniciais:
        guias_existentes = {c.get("numero_guia", "") for c in resultado["custas_pagas"]}
        for c in custas_iniciais:
            if c.get("numero_guia", "") and c["numero_guia"] not in guias_existentes:
                resultado["custas_pagas"].append(c)
                guias_existentes.add(c["numero_guia"])
            elif not c.get("numero_guia"):
                resultado["custas_pagas"].append(c)

    return resultado
