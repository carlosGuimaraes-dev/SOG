"""
Extrator inteligente de sentenças e sumários do PJE.

Foco: identificar quem foi condenado (sucumbente) e os encargos de custas/honorários
para preenchimento do SISTJWEB.

Regras de custas:
  - Custas iniciais: paga o autor (quem iniciou o processo), salvo gratuidade deferida
  - Se autor perdeu (condenado): abatimento no final
  - Se réu perdeu (condenado): paga custas finais + custas iniciais
"""
import re
import json
import hashlib
from typing import List, Dict, Any, Optional

try:
    import openai
    _OPENAI_DISPONIVEL = True
except ImportError:
    openai = None
    _OPENAI_DISPONIVEL = False

try:
    from config import OPENAI_API_KEY, OPENAI_MODEL, LLM_MAX_TOKENS, LLM_TEMPERATURE
except ImportError:
    from agente.src.config import OPENAI_API_KEY, OPENAI_MODEL, LLM_MAX_TOKENS, LLM_TEMPERATURE

try:
    from utils.logger import erro
except ImportError:

    def erro(mensagem: str, **kwargs: Any) -> None:
        pass


# ========================================================================
# CAMADA 1: Extração do Sumário/Capa
# ========================================================================

def extrair_ids_por_tipo(docs: List[Dict[str, Any]], tipos: List[str]) -> str:
    """Concatena IDs de documentos que correspondem aos tipos informados.
    
    Match exato no campo 'tipo' ou match exato no 'nome' (case-insensitive).
    """
    ids = []
    for d in docs:
        tipo_doc = d.get("tipo", "")
        nome_doc = d.get("nome", "")
        if tipo_doc in tipos:
            ids.append(str(d["doc_id"]))
            continue
        nome_upper = nome_doc.upper()
        for t in tipos:
            if t.upper() == nome_upper:
                ids.append(str(d["doc_id"]))
                break
    return ",".join(ids)


# ========================================================================
# CAMADA 1: Regex por Área do Direito
# ========================================================================

# ---- Cível ----
# Sucumbente: quem foi condenado a pagar (exclui custas/honorários do contexto)
# Bounds nos quantificadores para evitar backtracking catastrófico em textos longos.
RE_CIVEL_SUCUMBENTE = re.compile(
    r"condeno\s+(?:(?:o\s+(?:r[eé]u|autor|embargad[oa])|a)\s+)?([A-ZÁÉÍÓÚÃÕÀÂÊÎÔÛÇ][A-ZÁÉÍÓÚÃÕÀÂÊÎÔÛÇa-záéíóúãõàâêîôûç\s\.]{1,200}?)\s+ao\s+cumprimento[^.]{0,100}montante\s+de\s+R\$",
    re.IGNORECASE | re.DOTALL,
)
RE_CIVEL_SUCUMBENTE_FALLBACK = re.compile(
    r"condeno\s+(?:(?:o\s+(?:r[eé]u|autor|embargad[oa])|a)\s+)?([A-ZÁÉÍÓÚÃÕÀÂÊÎÔÛÇ][A-ZÁÉÍÓÚÃÕÀÂÊÎÔÛÇa-záéíóúãõàâêîôûç\s\.]{1,200}?)\s+ao\s+(?:cumprimento|pagamento)",
    re.IGNORECASE,
)
RE_CIVEL_VALOR_CONDENACAO = re.compile(
    r"(?:valor\s+d[ae]\s+condena[çc][ãa]o\s+de\s+R\$\s*([\d.,]+)"
    r"|condeno.*?ao\s+cumprimento.*?montante\s+de\s+R\$\s*([\d.,]+)"
    r"|montante\s+de\s+R\$\s*([\d.,]+))",
    re.IGNORECASE | re.DOTALL,
)
RE_CIVEL_HONORARIOS = re.compile(
    r"honor[áa]rios[^%]+?(\d+(?:,\d+)?)\s*%",
    re.IGNORECASE,
)
RE_CIVEL_SUSPENSAO_98 = re.compile(
    r"art(?:igo)?\.?\s*98[^§]{0,30}§\s*3",
    re.IGNORECASE | re.DOTALL,
)

# ---- Trabalhista ----
RE_TRAB_SUCUMBENTE = re.compile(
    r"condeno\s+(?:a\s+)?(?:reclamada|empregadora|r[eé]u)\s+([A-ZÁÉÍÓÚÃÕÀÂÊÎÔÛÇ][A-ZÁÉÍÓÚÃÕÀÂÊÎÔÛÇa-záéíóúãõàâêîôûç\s\.]+?)\s+ao\s+pagamento",
    re.IGNORECASE,
)
RE_TRAB_VALOR_TOTAL = re.compile(
    r"total\s+d[ae]\s+condena[çc][ãa]o[^R$]{0,100}R\$\s*([\d.,]+)",
    re.IGNORECASE | re.DOTALL,
)
RE_TRAB_HONORARIOS = re.compile(
    r"honor[áa]rios(?:\s+sucumbenciais)?[^\d]{0,80}(\d+(?:,\d+)?)\s*%",
    re.IGNORECASE | re.DOTALL,
)


def extrair_sentenca_regex(texto: str, area: str = "civel") -> Dict[str, Any]:
    """
    Extrai do DISPOSITIVO da sentença:
      - sucumbente_nome: quem foi condenado
      - sucumbente_tipo: autor, réu, reclamada, etc.
      - valor_condenacao: valor principal
      - honorarios_percentual: % de honorários
      - suspensao_exigibilidade: True se art. 98, § 3º (gratuidade)
    """
    resultado = {
        "sucumbente_nome": "",
        "sucumbente_tipo": "",
        "valor_condenacao": "",
        "honorarios_percentual": "",
        "suspensao_exigibilidade": False,
        "_score": 0.0,
        "_metodo": "regex",
        "_area": area,
    }

    if area == "civel":
        # Sucumbente: condenação principal (com "montante de R$")
        m = RE_CIVEL_SUCUMBENTE.search(texto)
        if not m:
            # Fallback: primeira condenação sem custas/honorários no contexto
            for match in RE_CIVEL_SUCUMBENTE_FALLBACK.finditer(texto):
                ctx = texto[match.start():match.end()+80].lower()
                if "custas" not in ctx and "honorários" not in ctx and "honorarios" not in ctx:
                    m = match
                    break
            if not m:
                m = RE_CIVEL_SUCUMBENTE_FALLBACK.search(texto)
        if m:
            resultado["sucumbente_nome"] = m.group(1).strip().replace("\n", " ")
            # Inferência de tipo
            trecho = texto[max(0, m.start()-50):m.start()].upper()
            if "RÉU" in trecho or "RÉ" in trecho or "REQUERIDA" in trecho:
                resultado["sucumbente_tipo"] = "réu"
            elif "AUTOR" in trecho or "REQUERENTE" in trecho:
                resultado["sucumbente_tipo"] = "autor"
            else:
                resultado["sucumbente_tipo"] = "réu"  # default em ações cíveis

        # Valor da condenação
        m = RE_CIVEL_VALOR_CONDENACAO.search(texto)
        if m:
            valor = next((g for g in m.groups() if g), "")
            resultado["valor_condenacao"] = valor.rstrip(".,;")

        # Honorários
        m = RE_CIVEL_HONORARIOS.search(texto)
        if m:
            resultado["honorarios_percentual"] = m.group(1)

        # Suspensão art. 98 (gratuidade de justiça)
        if RE_CIVEL_SUSPENSAO_98.search(texto):
            resultado["suspensao_exigibilidade"] = True

    elif area == "trabalhista":
        # Sucumbente
        m = RE_TRAB_SUCUMBENTE.search(texto)
        if m:
            resultado["sucumbente_nome"] = m.group(1).strip()
            resultado["sucumbente_tipo"] = "reclamada"

        # Valor (prioriza total da condenação)
        m_total = RE_TRAB_VALOR_TOTAL.search(texto)
        if m_total:
            resultado["valor_condenacao"] = m_total.group(1).rstrip(".")
        else:
            # Fallback: primeiro valor após CONDENO
            m = re.search(r"CONDENO.*?R\$\s*([\d.,]+)", texto, re.IGNORECASE | re.DOTALL)
            if m:
                resultado["valor_condenacao"] = m.group(1).rstrip(".")

        # Honorários
        m = RE_TRAB_HONORARIOS.search(texto)
        if m:
            resultado["honorarios_percentual"] = m.group(1)

        # Gratuidade
        if re.search(r"gratuidade\s+de\s+justi[çc]a", texto, re.IGNORECASE):
            resultado["suspensao_exigibilidade"] = True

    # Score: 3 campos obrigatórios (sucumbente, valor, honorários)
    campos = ["sucumbente_nome", "valor_condenacao", "honorarios_percentual"]
    preenchidos = sum(1 for c in campos if resultado[c])
    resultado["_score"] = preenchidos / len(campos)

    return resultado


# ========================================================================
# CAMADA 2: LLM Fallback
# ========================================================================

_PROMPT_CIVEL = """Você é um assistente jurídico especializado em extrair dados do DISPOSITIVO de sentenças judiciais brasileiras para preenchimento do sistema SISTJWEB de custas processuais.

Extraia do texto abaixo APENAS estes campos JSON:
- sucumbente_nome: nome da parte condenada (quem perdeu a ação e deve pagar)
- sucumbente_tipo: "autor" ou "réu" (quem perdeu)
- valor_condenacao: valor monetário da condenação (ex: "10.158,00")
- honorarios_percentual: percentual de honorários de sucumbência (ex: "10")
- suspensao_exigibilidade: true se houver deferimento de gratuidade de justiça (art. 98, § 3º CPC), false caso contrário

Regras:
1. O sucumbente é quem foi CONDENADO no dispositivo (ex: "CONDENO X ao pagamento").
2. Se a sentença condena o autor, sucumbente_tipo = "autor". Se condena o réu, = "réu".
3. Ignore condenações de custas processuais ou honorários advocatícios — foque na condenação principal.
4. Retorne APENAS o JSON, sem markdown, sem explicações.

Texto do dispositivo:
---
{texto}
---
"""

_PROMPT_TRABALHISTA = """Você é um assistente jurídico especializado em extrair dados do DISPOSITIVO de sentenças trabalhistas brasileiras para preenchimento do sistema SISTJWEB de custas processuais.

Extraia do texto abaixo APENAS estes campos JSON:
- sucumbente_nome: nome da parte condenada (reclamada/empregadora)
- sucumbente_tipo: sempre "reclamada"
- valor_condenacao: valor total da condenação (ex: "25.000,00")
- honorarios_percentual: percentual de honorários de sucumbência (ex: "10")
- suspensao_exigibilidade: true se houver gratuidade de justiça deferida, false caso contrário

Regras:
1. O sucumbente em ação trabalhista é sempre a reclamada (empregadora).
2. Valor da condenação = total de verbas condenatórias (não inclua honorários).
3. Retorne APENAS o JSON, sem markdown, sem explicações.

Texto do dispositivo:
---
{texto}
---
"""


def _chamar_llm(texto: str, area: str) -> Dict[str, Any]:
    """Chama LLM (OpenAI) para extrair campos quando regex falha.
    
    Retorna dict com os mesmos campos do regex. Se API indisponível,
    retorna dict vazio (código chamador ignora silenciosamente).
    """
    if not _OPENAI_DISPONIVEL or not OPENAI_API_KEY:
        return {}

    prompt = _PROMPT_CIVEL if area == "civel" else _PROMPT_TRABALHISTA
    prompt = prompt.format(texto=texto[:4000])  # limite de contexto

    try:
        cliente = openai.OpenAI(api_key=OPENAI_API_KEY)
        resposta = cliente.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Você é um extrator jurídico especializado. Responda apenas em JSON."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=LLM_MAX_TOKENS,
            temperature=LLM_TEMPERATURE,
            response_format={"type": "json_object"},
        )
        conteudo = resposta.choices[0].message.content or "{}"
        try:
            llm_json = json.loads(conteudo)
        except json.JSONDecodeError:
            erro(f"Resposta LLM inválida (JSONDecodeError): {conteudo[:200]!r}")
            return {}

        # Normaliza campos
        resultado = {
            "sucumbente_nome": str(llm_json.get("sucumbente_nome", "")).strip(),
            "sucumbente_tipo": str(llm_json.get("sucumbente_tipo", "")).strip().lower(),
            "valor_condenacao": str(llm_json.get("valor_condenacao", "")).strip(),
            "honorarios_percentual": str(llm_json.get("honorarios_percentual", "")).strip(),
            "suspensao_exigibilidade": bool(llm_json.get("suspensao_exigibilidade", False)),
        }
        return resultado
    except Exception:
        # Falha silenciosa — código chamador mantém o que regex conseguiu
        return {}


def extrair_sentenca(texto: str, area: str = "civel", forcar_llm: bool = False) -> Dict[str, Any]:
    """Extrai sentença: regex → LLM fallback se score < 0.5."""
    resultado = extrair_sentenca_regex(texto, area)

    if forcar_llm or resultado["_score"] < 0.5:
        try:
            llm_result = _chamar_llm(texto, area)
            for key in llm_result:
                if forcar_llm or not resultado.get(key):
                    resultado[key] = llm_result[key]
            resultado["_metodo"] = "llm"
        except NotImplementedError:
            pass

    return resultado


# ========================================================================
# CAMADA 3: Cache / Aprendizado
# ========================================================================

_cache_padroes: Dict[str, Dict[str, Any]] = {}


def _hash_texto(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()[:32]


def salvar_padrao(texto: str, resultado: Dict[str, Any], metodo: str, score: float) -> None:
    h = _hash_texto(texto)
    _cache_padroes[h] = {"hash": h, "resultado": resultado, "metodo": metodo, "score": score}


def buscar_padrao(texto: str) -> Optional[Dict[str, Any]]:
    h = _hash_texto(texto)
    return _cache_padroes.get(h)


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


def aplicar_correcao(texto: str, correcao: Dict[str, Any]) -> None:
    h = _hash_texto(texto)
    if h in _cache_padroes:
        _cache_padroes[h]["resultado"].update(correcao)
        _cache_padroes[h]["score"] = 1.0


# ========================================================================
# CAMADA 4: Integração Completa (Sumário + Sentença)
# ========================================================================

def extrair_completo(
    sumario: List[Dict[str, Any]],
    texto_sentenca: str,
    area: str = "civel",
) -> Dict[str, Any]:
    """
    Integra sumário + sentença. Retorna dict unificado para o SISTJWEB.
    """
    resultado = extrair_sentenca(texto_sentenca, area)

    # IDs do sumário
    resultado["ids_mandados"] = extrair_ids_por_tipo(sumario, ["Mandado"])
    resultado["ids_oficios"] = extrair_ids_por_tipo(sumario, ["Ofício"])
    resultado["ids_alvaras"] = extrair_ids_por_tipo(sumario, ["Alvará"])
    resultado["ids_traslados"] = extrair_ids_por_tipo(sumario, ["Traslado"])
    resultado["ids_diligencias"] = extrair_ids_por_tipo(sumario, ["Diligência"])
    resultado["ids_ar"] = extrair_ids_por_tipo(sumario, ["AR"])
    resultado["ids_armp"] = extrair_ids_por_tipo(sumario, ["AR/MP"])
    resultado["ids_sentenca"] = extrair_ids_por_tipo(sumario, ["Sentença"])
    resultado["ids_comprovante_custas"] = extrair_ids_por_tipo(
        sumario, ["Comprovante de Pagamento de Custas", "Comprovante de Pagamento das Custas"]
    )
    resultado["ids_decisoes"] = extrair_ids_por_tipo(sumario, ["Decisão"])

    return resultado
