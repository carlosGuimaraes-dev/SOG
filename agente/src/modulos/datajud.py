"""
Consulta à API pública Datajud (CNJ) para obter dados do processo.
"""
import requests
from typing import Dict, Any, Optional
from config import DATAJUD_API_KEY, DATAJUD_URL


def consultar(numero_sem_mascara: str) -> Dict[str, Any]:
    """
    Consulta o processo na API Datajud.
    Retorna dict com: data_distribuicao, polo_ativo, polo_passivo,
    valor_causa, classe, instancia.
    """
    headers = {
        "Authorization": f"APIKey {DATAJUD_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "query": {
            "match": {"numeroProcesso": numero_sem_mascara}
        }
    }

    resp = requests.post(DATAJUD_URL, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    hits = data.get("hits", {}).get("hits", [])
    if not hits:
        return {}

    source = hits[0].get("_source", {})

    # Detecta instância pelo segmento TT (posições 14-15 do número CNJ)
    segmento = numero_sem_mascara[13:15] if len(numero_sem_mascara) >= 15 else ""
    instancia = "1ª Instância" if segmento == "07" else "2ª Instância" if segmento == "08" else ""

    # Partes
    partes = source.get("partes", [])
    polo_ativo = ""
    polo_passivo = "Não Há"
    for parte in partes:
        tipo = parte.get("tipo", "").upper()
        if tipo == "AUTOR":
            polo_ativo = parte.get("nome", "")
        elif tipo == "REU":
            polo_passivo = parte.get("nome", "")

    valor_causa = source.get("valorCausa", "")
    if valor_causa:
        # Formata para o padrão brasileiro
        try:
            v = float(valor_causa)
            valor_causa = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except (ValueError, TypeError):
            pass

    return {
        "data_distribuicao": source.get("dataAjuizamento", ""),
        "polo_ativo": polo_ativo,
        "polo_passivo": polo_passivo,
        "valor_causa": valor_causa,
        "classe": source.get("classe", {}).get("nome", ""),
        "instancia": instancia,
    }
