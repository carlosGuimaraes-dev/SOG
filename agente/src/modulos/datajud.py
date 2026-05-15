"""
Consulta à API pública Datajud (CNJ) para obter dados do processo.

Nota: A API Datajud não disponibiliza partes nem valor da causa para
todos os tribunais (ex: TJDFT). Esses campos devem ser obtidos via
capa do processo no PJE (PDF).
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

    # Detecta instância pelo segmento TT (posições 15-16 do número CNJ, 0-based 14:16)
    # Formato CNJ 20 dígitos: NNNNNNN(7) DD(2) AAAA(4) J(1) TR(2) OOOO(4)
    segmento = numero_sem_mascara[14:16] if len(numero_sem_mascara) >= 16 else ""
    instancia = "1ª Instância" if segmento == "07" else "2ª Instância" if segmento == "08" else ""

    # Partes — nem todos os tribunais disponibilizam via Datajud (ex: TJDFT)
    partes = source.get("partes", [])
    polo_ativo = ""
    polo_passivo = ""
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

    # Formata data de ajuizamento (AAAAMMDDHHMMSS → DD/MM/AAAA)
    data_ajuiz = source.get("dataAjuizamento", "")
    data_distribuicao = ""
    if len(data_ajuiz) >= 8:
        data_distribuicao = f"{data_ajuiz[6:8]}/{data_ajuiz[4:6]}/{data_ajuiz[0:4]}"

    return {
        "data_distribuicao": data_distribuicao,
        "polo_ativo": polo_ativo,
        "polo_passivo": polo_passivo,
        "valor_causa": valor_causa,
        "classe": source.get("classe", {}).get("nome", ""),
        "instancia": instancia,
    }
