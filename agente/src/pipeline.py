"""
Orquestrador do pipeline de custas processuais TJDFT.

Fluxo de uma iteração (rodar_pipeline):
1. Coleta lista de processos no PJE por etiqueta
2. Para cada novo processo:
   a. Consulta Datajud
   b. Coleta documentos no PJE
   c. Parse dos documentos
   d. Preenche SISTJWEB
   e. Notifica operador
3. Emite processos aprovados (chamado pelo servico.py)
4. Logs em JSON estruturado

Este módulo é importável sem side-effects (sem execução no import).
"""
import os
import re
import tempfile
from typing import Dict, Any, List, Tuple, Optional

from config import MAX_TENTATIVAS
from banco import db
from modulos.pje import PjeClient
from modulos.datajud import consultar as datajud_consultar
from modulos.parser import processar_documentos
from modulos.extrator_pdf import extrair_texto_pdf
from modulos.sistjweb import SistjClient
from regras import detectar_area, obter_regras_outros_itens
from utils.logger import info, erro, aviso
from utils.notificador import enviar_alerta


def _obter_ou_criar_processo(
    numero: str,
    numero_sem_mascara: str,
    rearmado: bool = False,
) -> int:
    """Retorna o ID do processo existente ou cria um novo."""
    existente = db.processo_existe(numero)
    if existente:
        processo_id = existente["id"]
        if rearmado:
            db.atualizar_status(processo_id, "pendente", erro_msg="", incrementar_tentativa=False)
            db.registrar_log(processo_id, "reprocessamento", "ok", "Reprocessamento rearmado consumido no ciclo")
            return processo_id
        if existente["status"] not in {"erro", "pendente"}:
            info(f"Processo {numero} já existe com status '{existente['status']}'. Pulando.")
            db.registrar_log(
                processo_id,
                "pipeline",
                "aviso",
                f"Skip idempotente: status {existente['status']} já tratado",
            )
            return 0
        if existente["status"] == "pendente":
            dados_existentes = db.obter_dados_processo(processo_id)
            if dados_existentes:
                info(f"Processo {numero} já possui dados salvos. Pulando rerun normal.")
                db.registrar_log(
                    processo_id,
                    "pipeline",
                    "aviso",
                    "Skip idempotente: dados do processo já salvos",
                )
                return 0
            return processo_id
        db.atualizar_status(processo_id, "pendente", erro_msg="", incrementar_tentativa=True)
        return processo_id
    processo_id = db.inserir_processo(numero, numero_sem_mascara)
    info(f"Novo processo inserido: {numero} (id={processo_id})")
    return processo_id


def _coletar_datajud(numero: str, numero_sem_mascara: str, processo_id: int) -> Dict[str, Any]:
    """Consulta Datajud e registra log. Retorna dict com dados."""
    info(f"[{numero}] Consultando Datajud...", processo_id=processo_id, etapa="datajud")
    dados = datajud_consultar(numero_sem_mascara)
    status = "ok" if dados else "aviso"
    info(f"[{numero}] Datajud retornou {len(dados)} campo(s).", processo_id=processo_id, etapa="datajud")
    db.registrar_log(processo_id, "datajud", status, f"campos={len(dados)}")
    return dados


def _coletar_documentos(numero: str, processo_id: int, pje: PjeClient) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    """Coleta documentos no PJE e extrai textos. Retorna (docs, textos)."""
    info(f"[{numero}] Coletando documentos no PJE...", processo_id=processo_id, etapa="pje")
    docs, textos = pje.coletar_documentos(numero)
    for doc in docs:
        db.salvar_documento(
            processo_id, doc["doc_id"], doc["tipo"], doc["data_assinatura"], doc["nome"]
        )
    db.registrar_log(processo_id, "pje_documentos", "ok", f"{len(docs)} documentos")
    return docs, textos


def _construir_payload(
    numero: str,
    numero_sem_mascara: str,
    dados_datajud: Dict[str, Any],
    dados_parser: Dict[str, Any],
    area: str,
) -> Dict[str, Any]:
    """Monta o payload para preenchimento do SISTJWEB."""
    custas_pagas: List[Dict[str, Any]] = list(dados_parser.get("custas_pagas", []))

    return {
        "numero_sem_mascara": numero_sem_mascara,
        "numero": numero,
        "instancia": dados_datajud.get("instancia", "1ª Instância"),
        "processo_eletronico": 1,
        "circunscricao": "",
        "competencia": "",
        "feito": "",
        "classe": dados_datajud.get("classe", ""),
        "valor_causa": dados_datajud.get("valor_causa", ""),
        "data_distribuicao": dados_datajud.get("data_distribuicao", ""),
        "polo_ativo": dados_datajud.get("polo_ativo", ""),
        "polo_passivo": dados_datajud.get("polo_passivo", "Não Há"),
        "tipo_guia": "",
        "pro_rata": 1 if len(dados_parser.get("sucumbentes", [])) > 1 else 0,
        "sucumbentes": [
            {
                "nome": dados_parser.get("sucumbente_nome", ""),
                "cpf_cnpj": dados_parser.get("sucumbente_cpf_cnpj", ""),
                "tipo": dados_parser.get("sucumbente_tipo", "Requerido"),
                "is_autor": False,
                "percentual": dados_parser.get("honorarios_percentual", "100"),
            }
        ],
        **dados_parser,
        "custas_pagas": custas_pagas,
        "area_direito": area,
    }


def _preencher_sistj(numero: str, processo_id: int, payload: Dict[str, Any], sistj: SistjClient):
    """Preenche SISTJWEB, salva dados e atualiza status."""
    info(f"[{numero}] Preenchendo SISTJWEB...", processo_id=processo_id, etapa="sistjweb")
    if not sistj.login():
        raise RuntimeError("Falha no login SISTJWEB")

    resultado_sistj = sistj.preencher(payload, numero)

    dados_salvar = {
        chave: valor
        for chave, valor in {**payload, **resultado_sistj}.items()
        if chave in db.COLUNAS_PERMITIDAS_DADOS_PROCESSO
    }
    db.salvar_dados_processo(processo_id, dados_salvar)
    db.atualizar_status(processo_id, "aguardando_aprovacao")
    db.registrar_log(processo_id, "sistjweb", "ok", f"Screenshot: {resultado_sistj.get('screenshot_path', '')}")
    info(f"[{numero}] Pipeline concluído. Aguardando aprovação.", processo_id=processo_id)


def _notificar_erro(numero: str, processo_id: Optional[int], erro_msg: str):
    """Registra erro, atualiza status e notifica operador se necessário."""
    erro(f"[{numero}] Erro no pipeline: {erro_msg}", processo_id=processo_id)
    if processo_id:
        db.atualizar_status(processo_id, "erro", erro_msg, incrementar_tentativa=True)
        db.registrar_log(processo_id, "pipeline", "erro", erro_msg)
        proc = db.processo_existe(numero)
        if proc and proc.get("tentativas", 0) >= MAX_TENTATIVAS:
            enviar_alerta([{"numero": numero, "status": "erro"}])


def processar_processo(
    numero: str,
    numero_sem_mascara: str,
    pje: PjeClient,
    sistj: SistjClient,
    rearmado: bool = False,
):
    """Executa o pipeline completo para um único processo."""
    processo_id = None
    try:
        processo_id = _obter_ou_criar_processo(numero, numero_sem_mascara, rearmado=rearmado)
        if processo_id == 0:
            return

        db.registrar_log(processo_id, "inicio", "ok", "Iniciando pipeline")

        dados_datajud = _coletar_datajud(numero, numero_sem_mascara, processo_id)
        docs, textos = _coletar_documentos(numero, processo_id, pje)

        # ── Extração de custas iniciais a partir de PDFs ──
        custas_extraidas: List[Dict[str, Any]] = []
        tipos_custas = {"Comprovante de Pagamento de Custas", "Guia"}
        with tempfile.TemporaryDirectory() as tmpdir:
            for doc in docs:
                if doc.get("tipo", "") not in tipos_custas:
                    continue
                pdf_path = os.path.join(tmpdir, f"{doc['doc_id']}.pdf")
                if not pje.baixar_documento_pdf(doc["doc_id"], pdf_path):
                    continue

                resultado_pdf = extrair_texto_pdf(pdf_path)
                custas = resultado_pdf.get("custas_iniciais", {})

                if custas.get("scanned"):
                    aviso(
                        f"PDF de custas do doc {doc['doc_id']} é scanned. Ignorando.",
                        processo_id=processo_id,
                    )
                    db.registrar_log(
                        processo_id, "custas_pdf", "aviso",
                        f"doc_id={doc['doc_id']} scanned"
                    )
                    continue

                if custas.get("encontrado"):
                    entrada = {
                        "data": custas.get("vencimento", ""),
                        "valor": custas.get("valor_total", ""),
                        "numero_guia": custas.get("numero_guia", ""),
                    }
                    custas_extraidas.append(entrada)
                    info(
                        f"Custas iniciais extraídas do doc {doc['doc_id']}: "
                        f"valor={entrada['valor']} guia={entrada['numero_guia']}",
                        processo_id=processo_id,
                    )
                    db.registrar_log(
                        processo_id, "custas_pdf", "ok",
                        f"doc_id={doc['doc_id']} valor={entrada['valor']} guia={entrada['numero_guia']}"
                    )

        info(f"[{numero}] Analisando documentos...", processo_id=processo_id, etapa="parser")
        dados_parser = processar_documentos(docs, textos, custas_iniciais=custas_extraidas)
        info(f"[{numero}] Parser retornou {len(dados_parser)} campo(s).", processo_id=processo_id, etapa="parser")
        db.registrar_log(processo_id, "parser", "ok", f"campos={len(dados_parser)}")

        area = detectar_area(dados_datajud.get("classe", ""), "")
        regras = obter_regras_outros_itens(area)

        if not regras and area == "default":
            aviso(f"Área não mapeada para {numero}. Status: pendente_manual.", processo_id=processo_id)
            db.atualizar_status(processo_id, "pendente_manual")
            db.registrar_log(processo_id, "regras", "aviso", "Área não mapeada")
            return

        payload = _construir_payload(
            numero, numero_sem_mascara, dados_datajud, dados_parser, area,
        )
        _preencher_sistj(numero, processo_id, payload, sistj)

    except Exception as exc:
        _notificar_erro(numero, processo_id, str(exc))


def rodar_pipeline(pje: PjeClient, sistj: SistjClient, ciclo_uuid: Optional[str] = None) -> None:
    """
    Executa UMA iteração completa do pipeline:
    1. Coleta lista de processos no PJE por etiqueta
    2. Processa cada processo novo
    3. Notifica operador sobre pendentes de aprovação

    Args:
        pje: Instância de PjeClient já autenticada (ou a ser autenticada).
        sistj: Instância de SistjClient já autenticada (ou a ser autenticada).
    """
    info("Iniciando iteração do pipeline de custas TJDFT...")

    if ciclo_uuid:
        membros = db.listar_membros_ciclo(ciclo_uuid)
        membros_por_numero = {m["numero"]: m for m in membros}
        numeros = [m["numero"] for m in membros]
        info(f"Total de processos no ciclo {ciclo_uuid}: {len(numeros)}")
    else:
        membros_por_numero = {}
        numeros = pje.coletar_lista_processos()
        info(f"Total de processos na etiqueta: {len(numeros)}")

    if not numeros:
        info("Nenhum processo novo encontrado.")
        return

    for numero in numeros:
        numero_sem_mascara = re.sub(r"\D", "", numero)
        membro = membros_por_numero.get(numero)
        if membro and membro.get("processado_em"):
            info(f"Processo {numero} já foi processado no ciclo {ciclo_uuid}. Pulando.")
            db.registrar_log(
                membro["processo_id"],
                "pipeline",
                "aviso",
                "Skip idempotente: membro do ciclo já processado",
            )
            continue
        rearmado = bool(membro and membro.get("origem") == "rearmado")
        try:
            processar_processo(numero, numero_sem_mascara, pje, sistj, rearmado=rearmado)
            if ciclo_uuid and membro:
                db.marcar_membro_ciclo_processado(ciclo_uuid, membro["processo_id"])
        except Exception as e:
            erro(f"Erro inesperado processando {numero}: {e}")
            if ciclo_uuid and membro:
                db.marcar_membro_ciclo_processado(ciclo_uuid, membro["processo_id"])
            continue

    pendentes = db.listar_aguardando_aprovacao()
    if pendentes:
        enviar_alerta(pendentes)

    if ciclo_uuid:
        db.atualizar_contadores_ciclo(ciclo_uuid)

    info("Iteração do pipeline finalizada.")
