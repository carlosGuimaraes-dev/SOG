"""
Executor de tarefas sob demanda do agente.
Mapeia tipos de tarefa para funções que usam PjeClient/SistjClient.
"""
import re
from pathlib import Path
from typing import Dict, Any, Callable

from banco import db
from config import DEMONSTRATIVOS_DIR
from modulos.pje import PjeClient
from modulos.sistjweb import SistjClient
from pipeline import processar_processo, _construir_payload
from regras import detectar_area

# Registry de handlers
_HANDLERS: Dict[str, Callable] = {}


def registrar(tipo: str):
    """Decorador para registrar handler de tarefa."""
    def wrapper(fn: Callable):
        _HANDLERS[tipo] = fn
        return fn
    return wrapper


def executar_tarefa(tarefa: Dict[str, Any], pje: PjeClient, sistj: SistjClient) -> Dict[str, Any]:
    """Executa uma tarefa e retorna o resultado."""
    tipo = tarefa["tipo"]
    payload = tarefa.get("payload") or {}

    handler = _HANDLERS.get(tipo)
    if not handler:
        raise ValueError(f"Tipo de tarefa desconhecido: {tipo}")

    return handler(payload, pje, sistj)


def tipos_suportados() -> list:
    return list(_HANDLERS.keys())


# ── Handlers ──────────────────────────────────────────────────────────────


def _obter_processo(processo_id: int) -> Dict[str, Any]:
    processo = db.obter_processo(processo_id)
    if not processo:
        raise ValueError(f"Processo {processo_id} não encontrado")
    return processo


def _obter_dados_processo(processo_id: int) -> Dict[str, Any]:
    dados = db.obter_dados_processo(processo_id)
    if not dados:
        raise ValueError(f"Dados do processo {processo_id} não encontrados")
    return dados


@registrar("consultar_etiqueta_pje")
def _consultar_etiqueta_pje(payload, pje, sistj):
    pje.garantir_autenticado()
    numeros = pje.coletar_lista_processos()
    return {"processos": numeros, "total": len(numeros)}

@registrar("verificar_sessao_pje")
def _verificar_sessao_pje(payload, pje, sistj):
    page = getattr(pje, "page", None)
    if not page:
        return {
            "estado": "pending",
            "logado": False,
            "url_atual": None,
            "mensagem": "Login pendente no PJe. Abra a sessao no navegador do SOG para validar.",
        }
    try:
        logado = pje._esta_logado(page)
        return {
            "estado": "active" if logado else "expired",
            "logado": logado,
            "url_atual": page.url,
            "mensagem": (
                "Sessao ativa"
                if logado
                else "Sessao expirada no PJe. Reabra a sessao no navegador do SOG."
            ),
        }
    except Exception:
        return {
            "estado": "unavailable",
            "logado": False,
            "url_atual": None,
            "mensagem": "Validacao do PJe indisponivel no momento.",
        }


@registrar("consultar_documentos_pje")
def _consultar_documentos_pje(payload, pje, sistj):
    numero = payload["numero_processo"]
    pje.garantir_autenticado()
    docs, textos = pje.coletar_documentos(numero)
    return {
        "numero_processo": numero,
        "documentos": docs,
        "textos": textos,
        "total": len(docs),
    }


@registrar("baixar_pdf_pje")
def _baixar_pdf_pje(payload, pje, sistj):
    numero = payload["numero_processo"]
    doc_id = payload["doc_id"]
    pje.garantir_autenticado()
    pje.coletar_documentos(numero)

    DEMONSTRATIVOS_DIR.mkdir(parents=True, exist_ok=True)
    numero_limpo = re.sub(r"\D", "", numero)
    caminho_pdf = Path(DEMONSTRATIVOS_DIR) / f"{numero_limpo}_{doc_id}.pdf"

    sucesso = pje.baixar_documento_pdf(doc_id, str(caminho_pdf))
    if not sucesso:
        raise RuntimeError(f"Não foi possível baixar o PDF do documento {doc_id}")

    return {
        "sucesso": True,
        "numero_processo": numero,
        "doc_id": doc_id,
        "caminho_pdf": str(caminho_pdf),
    }


@registrar("reautenticar_pje")
def _reautenticar_pje(payload, pje, sistj):
    pje.reautenticar_interativo()
    return {"logado": True}


@registrar("verificar_sessao_sistj")
def _verificar_sessao_sistj(payload, pje, sistj):
    page = getattr(sistj, "page", None)
    if not page:
        return {
            "estado": "pending",
            "logado": False,
            "url_atual": None,
            "mensagem": "Login pendente no SISTJWEB. Abra a sessao no navegador do SOG para validar.",
        }
    try:
        logado = sistj._esta_logado(page)
        return {
            "estado": "active" if logado else "expired",
            "logado": logado,
            "url_atual": page.url,
            "mensagem": (
                "Sessao ativa"
                if logado
                else "Sessao expirada no SISTJWEB. Reabra a sessao no navegador do SOG."
            ),
        }
    except Exception:
        return {
            "estado": "unavailable",
            "logado": False,
            "url_atual": None,
            "mensagem": "Validacao do SISTJWEB indisponivel no momento.",
        }


@registrar("reautenticar_sistj")
def _reautenticar_sistj(payload, pje, sistj):
    sistj.reautenticar_interativo()
    return {"logado": True}


@registrar("preencher_sistj")
def _preencher_sistj(payload, pje, sistj):
    processo_id = payload["processo_id"]
    dados = _obter_dados_processo(processo_id)
    processo = _obter_processo(processo_id)

    area = dados.get("area_direito") or detectar_area(dados.get("classe", ""), dados.get("feito", ""))
    payload_sistj = _construir_payload(
        processo.get("numero", dados.get("numero", "")),
        processo.get("numero_sem_mascara", dados.get("numero_sem_mascara", "")),
        dados,
        dados,
        area,
    )

    sistj.garantir_autenticado()
    resultado = sistj.preencher(payload_sistj, payload_sistj["numero"])

    dados_salvar = {
        chave: valor
        for chave, valor in {**payload_sistj, **resultado}.items()
        if chave in db.COLUNAS_PERMITIDAS_DADOS_PROCESSO
    }
    db.salvar_dados_processo(processo_id, dados_salvar)
    db.atualizar_status(processo_id, "aguardando_aprovacao")
    db.registrar_log(
        processo_id,
        "sistjweb",
        "ok",
        f"Screenshot: {resultado.get('screenshot_path', '')}",
    )

    return resultado


@registrar("gravar_aprovar_sistj")
def _gravar_aprovar_sistj(payload, pje, sistj):
    processo_id = payload["processo_id"]
    processo = _obter_processo(processo_id)
    numero = processo.get("numero", "")
    numero_sem_mascara = processo.get("numero_sem_mascara", "")

    evidencia = db.obter_evidencia_emissao(
        processo_id,
        db.ETAPA_EVIDENCIA_DEMONSTRATIVO_SISTJ,
    )
    if evidencia and not payload.get("confirmar_reemissao"):
        caminho_existente = evidencia.get("referencia_arquivo")
        if caminho_existente and Path(caminho_existente).exists():
            db.registrar_log(
                processo_id,
                "emissao",
                "aviso",
                "Skip idempotente: demonstrativo SISTJ já emitido",
                chave_idempotencia="emissao:sistj:skip",
            )
            return {
                "caminho_pdf": caminho_existente,
                "numero_processo": numero,
                "processo_id": processo_id,
                "skipped": True,
                "reason": "already_emitted_sistj",
            }

    sistj.garantir_autenticado()
    caminho_pdf = sistj.gravar_e_aprovar(numero_sem_mascara)
    db.salvar_evidencia_emissao(
        processo_id,
        db.ETAPA_EVIDENCIA_DEMONSTRATIVO_SISTJ,
        referencia_arquivo=caminho_pdf,
        referencia_externa=numero_sem_mascara,
        metadados={"origem": "sistjweb"},
    )
    db.registrar_log(
        processo_id,
        "sistjweb",
        "ok",
        f"PDF: {caminho_pdf}",
        chave_idempotencia="emissao:sistj:ok",
    )

    return {"caminho_pdf": caminho_pdf, "numero_processo": numero, "processo_id": processo_id}


@registrar("anexar_demonstrativo_pje")
def _anexar_demonstrativo_pje(payload, pje, sistj):
    processo_id = payload["processo_id"]
    processo = _obter_processo(processo_id)

    numero = processo.get("numero", "")
    numero_sem_mascara = processo.get("numero_sem_mascara", "")
    evidencia_anexo = db.obter_evidencia_emissao(
        processo_id,
        db.ETAPA_EVIDENCIA_ANEXO_PJE,
    )
    if evidencia_anexo and not payload.get("confirmar_reemissao"):
        if processo.get("status") != "emitido":
            db.atualizar_status(processo_id, "emitido")
        db.registrar_log(
            processo_id,
            "emissao",
            "aviso",
            "Skip idempotente: demonstrativo já anexado no PJe",
            chave_idempotencia="emissao:anexo_pje:skip",
        )
        return {
            "sucesso": False,
            "skipped": True,
            "reason": "already_attached_pje",
            "numero_processo": numero,
            "processo_id": processo_id,
        }

    if processo.get("status") == "emitido" and not payload.get("confirmar_reemissao"):
        db.registrar_log(
            processo_id,
            "emissao",
            "aviso",
            "Skip idempotente: demonstrativo já anexado no PJe",
            chave_idempotencia="emissao:anexo_pje:skip",
        )
        return {
            "sucesso": False,
            "skipped": True,
            "reason": "already_emitido",
            "numero_processo": numero,
            "processo_id": processo_id,
        }

    evidencia_demonstrativo = db.obter_evidencia_emissao(
        processo_id,
        db.ETAPA_EVIDENCIA_DEMONSTRATIVO_SISTJ,
    )
    candidatos = []
    if evidencia_demonstrativo and evidencia_demonstrativo.get("referencia_arquivo"):
        candidatos.append(Path(evidencia_demonstrativo["referencia_arquivo"]))

    candidatos.extend([
        Path(DEMONSTRATIVOS_DIR) / f"{numero_sem_mascara}.pdf",
        Path(DEMONSTRATIVOS_DIR) / f"{numero}.pdf",
        Path(DEMONSTRATIVOS_DIR) / f"{numero_sem_mascara}_sistjweb.pdf",
    ])
    caminho_pdf = next((p for p in candidatos if p.exists()), None)
    if not caminho_pdf:
        raise FileNotFoundError(f"PDF do demonstrativo não encontrado para {numero}")

    pje.garantir_autenticado()
    sucesso = pje.anexar_demonstrativo(numero, str(caminho_pdf))

    if sucesso:
        db.salvar_evidencia_emissao(
            processo_id,
            db.ETAPA_EVIDENCIA_ANEXO_PJE,
            referencia_arquivo=str(caminho_pdf),
            referencia_externa=numero,
            metadados={"origem": "pje"},
        )
        db.atualizar_status(processo_id, "emitido")
        db.registrar_log(
            processo_id,
            "emissao",
            "ok",
            f"Anexado: {caminho_pdf}",
            chave_idempotencia="emissao:anexo_pje:ok",
        )
    else:
        raise RuntimeError(f"Falha ao anexar demonstrativo no PJe para {numero}")

    return {
        "sucesso": sucesso,
        "caminho_pdf": str(caminho_pdf),
        "numero_processo": numero,
        "processo_id": processo_id,
    }


@registrar("reprocessar_processo")
def _reprocessar_processo(payload, pje, sistj):
    processo_id = payload["processo_id"]
    processo = _obter_processo(processo_id)
    numero = processo.get("numero", "")
    numero_sem_mascara = processo.get("numero_sem_mascara", "")

    db.atualizar_status(processo_id, "pendente", erro_msg="", incrementar_tentativa=False)
    processar_processo(numero, numero_sem_mascara, pje, sistj)
    return {"numero_processo": numero, "status": "reprocessado"}
