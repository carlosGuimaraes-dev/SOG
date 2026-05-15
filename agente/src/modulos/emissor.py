"""
Módulo emissor: após aprovação humana, aprova no SISTJWEB e anexa no PJE.
"""
from typing import Optional
from modulos.sistjweb import SistjClient
from modulos.pje import PjeClient
from banco import db
from utils.logger import info, erro


def emitir_e_anexar(processo_id: int) -> bool:
    """
    1. Reconecta ao SISTJWEB
    2. Navega até o processo salvo
    3. Clica 'Gravar e Aprovar'
    4. Baixa PDF do Demonstrativo
    5. Anexa no PJE
    6. Atualiza status para 'emitido'
    """
    processo = db.obter_dados_processo(processo_id)
    if not processo:
        erro(f"Dados do processo {processo_id} não encontrados.")
        return False

    numero = processo.get("numero", "")
    numero_sem_mascara = processo.get("numero_sem_mascara", "")

    sistj = SistjClient()
    pje = PjeClient()

    try:
        # SISTJWEB
        if not sistj.login():
            raise RuntimeError("Falha no login SISTJWEB")
        caminho_pdf = sistj.gravar_e_aprovar(numero_sem_mascara)

        # PJE
        if not pje.login():
            raise RuntimeError("Falha no login PJE")
        pje.anexar_demonstrativo(numero, caminho_pdf)

        db.atualizar_status(processo_id, "emitido")
        db.registrar_log(processo_id, "emissao", "ok", f"Demonstrativo anexado: {caminho_pdf}")
        info(f"Processo {numero} emitido e anexado com sucesso.")
        return True
    except Exception as e:
        db.atualizar_status(processo_id, "erro", str(e))
        db.registrar_log(processo_id, "emissao", "erro", str(e))
        erro(f"Erro na emissão do processo {numero}: {e}")
        return False
    finally:
        sistj.fechar()
        pje.fechar()
