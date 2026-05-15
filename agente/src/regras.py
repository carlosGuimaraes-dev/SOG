"""
Regras de negócio: combinações de itens da guia por área do direito.
"""
from typing import List, Dict, Any


REGRAS_OUTROS_ITENS = {
    "civel_comum": [
        {"item_guia": "Distribuidor", "item_calculo": "D-I-a", "quantidade": 1},
        {"item_guia": "Distribuidor", "item_calculo": "D-II-a", "quantidade": 1},
        {"item_guia": "Contador", "item_calculo": "E-I", "quantidade": 1},
        {
            "item_guia": "Ofícios",
            "item_calculo": "G-XX-a parte 2",
            "usa_ids_oficios": True,
            "quantidade": 1,
        },
        {
            "item_guia": "Custas",
            "item_calculo": "G-I",
            "usa_valor_causa_atualizado": True,
            "quantidade": 1,
        },
    ],
    "familia": [],
    "fazenda_publica": [],
    "criminal": [],
    "default": [],
}


def detectar_area(classe: str, feito: str) -> str:
    c = (classe or "").lower()
    f = (feito or "").lower()
    texto = c + " " + f

    if any(
        x in texto
        for x in ["família", "divórcio", "alimentos", "inventário", "partilha"]
    ):
        return "familia"
    if any(x in texto for x in ["fazenda", "tributário", "execução fiscal"]):
        return "fazenda_publica"
    if any(x in texto for x in ["criminal", "penal", "crime", "contravenção"]):
        return "criminal"
    if any(
        x in texto
        for x in ["procedimento comum", "indenização", "cobrança", "execução"]
    ):
        return "civel_comum"
    return "default"


def obter_regras_outros_itens(area: str) -> List[Dict[str, Any]]:
    return REGRAS_OUTROS_ITENS.get(area, [])
