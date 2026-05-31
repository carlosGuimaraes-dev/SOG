"""
Módulo emissor: após aprovação humana, aprova no SISTJWEB e anexa no PJE.

Versão adaptada para serviço longo: recebe clients já instanciados
em vez de criar novos a cada emissão.
"""
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

    numero = processo.get("numero", "")
    numero_sem_mascara = processo.get("numero_sem_mascara", "")
    processo_meta = db.obter_processo(processo_id)
    if processo_meta and processo_meta.get("status") == "emitido":
        db.registrar_log(
            processo_id,
            "emissao",
            "aviso",
            "Skip idempotente: demonstrativo já anexado no PJe",
        )
        info(f"Processo {numero} já emitido. Pulando anexo.")
        return True

    try:
        # SISTJWEB — já autenticado (garantir_autenticado é no-op se sessão viva)
        if not sistj.garantir_autenticado():
            raise RuntimeError("Falha na autenticação SISTJWEB")
        caminho_pdf = sistj.gravar_e_aprovar(numero_sem_mascara)

        # PJe
        if not pje.garantir_autenticado():
            raise RuntimeError("Falha na autenticação PJE")
        pje.anexar_demonstrativo(numero, caminho_pdf)

        db.atualizar_status(processo_id, "emitido")
        db.registrar_log(processo_id, "emissao", "ok", f"Demonstrativo: {caminho_pdf}")
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
