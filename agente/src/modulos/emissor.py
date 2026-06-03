"""
Módulo emissor: após aprovação humana, aprova no SISTJWEB e anexa no PJE.

Versão adaptada para serviço longo: recebe clients já instanciados
em vez de criar novos a cada emissão.
"""
from pathlib import Path
from typing import Optional
from sog_shared import db
from utils.logger import info, erro
from modulos.sistjweb import SistjClient
from modulos.pje import PjeClient


def emitir_e_anexar(processo_id: int, sistj: SistjClient, pje: PjeClient) -> bool:
    """
    1. Navega até o processo salvo no SISTJWEB
    2. Clica 'Gravar e Aprovar'
    3. Baixa PDF do Demonstrativo
    4. Anexa no PJe
    5. Atualiza status para 'emitido'
    """
    processo = db.obter_dados_processo(processo_id)
    if not processo:
        erro(f"Dados do processo {processo_id} não encontrados.")
        return False

    processo_meta = db.obter_processo(processo_id)
    numero = (processo_meta or {}).get("numero", "")
    numero_sem_mascara = (processo_meta or {}).get("numero_sem_mascara", "")
    evidencia_anexo = db.obter_evidencia_emissao(
        processo_id,
        db.ETAPA_EVIDENCIA_ANEXO_PJE,
    )
    if evidencia_anexo:
        if processo_meta and processo_meta.get("status") != "emitido":
            db.atualizar_status(processo_id, "emitido")
        db.registrar_log(
            processo_id,
            "emissao",
            "aviso",
            "Skip idempotente: demonstrativo já anexado no PJe",
            chave_idempotencia="emissao:anexo_pje:skip",
        )
        info(f"Processo {numero} já emitido. Pulando anexo.")
        return True

    try:
        # SISTJWEB — já autenticado (garantir_autenticado é no-op se sessão viva)
        if not sistj.garantir_autenticado():
            raise RuntimeError("Falha na autenticação SISTJWEB")
        evidencia_demonstrativo = db.obter_evidencia_emissao(
            processo_id,
            db.ETAPA_EVIDENCIA_DEMONSTRATIVO_SISTJ,
        )
        caminho_pdf = None
        if evidencia_demonstrativo:
            caminho_existente = evidencia_demonstrativo.get("referencia_arquivo")
            if caminho_existente and Path(caminho_existente).exists():
                caminho_pdf = caminho_existente
                db.registrar_log(
                    processo_id,
                    "emissao",
                    "aviso",
                    "Skip idempotente: demonstrativo SISTJ já emitido",
                    chave_idempotencia="emissao:sistj:skip",
                )

        if not caminho_pdf:
            caminho_pdf = sistj.gravar_e_aprovar(numero_sem_mascara)
            db.salvar_evidencia_emissao(
                processo_id,
                db.ETAPA_EVIDENCIA_DEMONSTRATIVO_SISTJ,
                referencia_arquivo=caminho_pdf,
                referencia_externa=numero_sem_mascara,
                metadados={"origem": "sistjweb"},
            )

        # PJe
        if not pje.garantir_autenticado():
            raise RuntimeError("Falha na autenticação PJE")
        if not pje.anexar_demonstrativo(numero, caminho_pdf):
            raise RuntimeError("Falha ao anexar demonstrativo no PJe")

        db.salvar_evidencia_emissao(
            processo_id,
            db.ETAPA_EVIDENCIA_ANEXO_PJE,
            referencia_arquivo=caminho_pdf,
            referencia_externa=numero,
            metadados={"origem": "pje"},
        )
        db.atualizar_status(processo_id, "emitido")
        db.registrar_log(
            processo_id,
            "emissao",
            "ok",
            f"Demonstrativo: {caminho_pdf}",
            chave_idempotencia="emissao:anexo_pje:ok",
        )
        info(f"Processo {numero} emitido e anexado com sucesso.")
        return True
    except Exception as e:
        db.atualizar_status(processo_id, "erro", str(e))
        db.registrar_log(processo_id, "emissao", "erro", str(e))
        erro(f"Erro na emissão do processo {numero}: {e}")
        return False


def emitir_pendentes(sistj: SistjClient, pje: PjeClient) -> None:
    """Processa todos os processos com status='aprovado'."""
    pendentes = db.listar_aprovados()
    if not pendentes:
        return

    info(f"Processando {len(pendentes)} emissões pendentes...")
    for proc in pendentes:
        emitir_e_anexar(proc["id"], sistj, pje)
