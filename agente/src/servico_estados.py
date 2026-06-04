from modulos.auth_manager import ReautenticacaoNecessariaError
from utils.logger import aviso, erro


def mensagem_captura_chrome(resultado: dict) -> str:
    reason = resultado.get("reason")
    if reason == "chrome_indisponivel":
        return "Aguardando Chrome de login. Clique em 'Abrir Chrome para login' no SOG Desktop."
    if reason == "abas_ausentes":
        faltando = ", ".join(resultado.get("missing", []))
        return f"Aguardando abas de login no Chrome: {faltando}."
    if reason == "login_pendente":
        pendente = ", ".join(resultado.get("pending", []))
        return f"Aguardando conclusão de login no Chrome: {pendente}."
    return "Aguardando login no Chrome monitorável."


def tratar_loop_iteration(
    servico,
    comando: str,
    status_db: str,
    tempo_dormir_segundos: int,
    tempo_erro_segundos: int,
    tempo_espera_curta_segundos: int,
) -> None:
    if _tratar_interrupcao_imediata(servico, comando, status_db):
        return
    handler = _handler_por_estado(status_db)
    if handler and handler(
        servico,
        comando,
        tempo_dormir_segundos,
        tempo_erro_segundos,
        tempo_espera_curta_segundos,
    ):
        return
    _aguardar_estado_desconhecido(servico, status_db, tempo_espera_curta_segundos)


def _tratar_interrupcao_imediata(servico, comando: str, status_db: str) -> bool:
    if servico._stop_event.is_set():
        if status_db != "parando":
            servico._set_status("parando", "Encerramento do processo recebido.")
        return True
    if comando == "parar" and status_db in {
        "iniciando",
        "autenticando",
        "executando",
        "dormindo",
    }:
        servico._pausar_ciclo("interrompido", "Ciclo pausado por solicitação do dashboard.")
        return True
    return False


def _handler_por_estado(status_db: str):
    handlers = {
        "parado": _tratar_estado_em_espera,
        "pausado": _tratar_estado_em_espera,
        "interrompido": _tratar_estado_em_espera,
        "erro_pausado": _tratar_estado_em_espera,
        "iniciando": _tratar_estado_iniciando,
        "autenticando": _tratar_estado_autenticando,
        "aguardando_login": _tratar_estado_aguardando_login,
        "executando": _tratar_estado_executando,
        "dormindo": _tratar_estado_dormindo,
        "erro": _tratar_estado_erro,
        "parando": _tratar_estado_parando,
    }
    return handlers.get(status_db)


def _tratar_estado_em_espera(servico, comando: str, _td: int, _te: int, tempo_curto: int) -> bool:
    if comando == "iniciar":
        servico._set_status("autenticando", "Iniciando autenticação...")
    else:
        _aguardar_curto(servico, tempo_curto)
    return True


def _tratar_estado_iniciando(servico, comando: str, _td: int, _te: int, _tc: int) -> bool:
    if comando != "iniciar":
        return False
    servico._set_status("autenticando", "Iniciando autenticação...")
    return True


def _tratar_estado_autenticando(servico, _comando: str, _td: int, _te: int, _tc: int) -> bool:
    try:
        servico._autenticar_todos()
        servico._fechar_ciclo_ativo()
        servico._set_status("executando", "Autenticação OK. Iniciando execução.")
    except ReautenticacaoNecessariaError as e:
        servico._pausar_ciclo("aguardando_login", f"Sessão {e.sistema} expirada. Faça login no navegador.")
    except Exception as e:
        erro(f"Falha na autenticação: {e}")
        servico._pausar_ciclo("erro_pausado", f"Falha na autenticação: {e}")
    return True


def _tratar_estado_aguardando_login(servico, comando: str, _td: int, _te: int, tempo_curto: int) -> bool:
    if comando != "iniciar":
        _aguardar_curto(servico, tempo_curto)
        return True
    try:
        if not servico._autenticar_interativo():
            _aguardar_curto(servico, tempo_curto)
            return True
        servico._fechar_ciclo_ativo()
        servico._set_status("executando", "Sessões Chrome capturadas. Retomando execução.")
    except Exception as e:
        erro(f"Falha ao capturar login no Chrome: {e}")
        servico._pausar_ciclo("erro_pausado", f"Falha ao capturar login no Chrome: {e}")
    return True


def _tratar_estado_executando(servico, _comando: str, _td: int, _te: int, _tc: int) -> bool:
    try:
        if _processar_tarefas_pendentes(servico):
            return True
        _finalizar_iteracao(servico)
    except ReautenticacaoNecessariaError as e:
        servico._pausar_ciclo("aguardando_login", f"Sessão {e.sistema} expirada durante execução.")
    except Exception as e:
        erro(f"Erro durante execução: {e}")
        servico._pausar_ciclo("erro_pausado", str(e))
    return True


def _processar_tarefas_pendentes(servico) -> bool:
    tarefas_processadas = servico._processar_tarefas_pendentes(max_tarefas=servico._tarefas_por_iteracao)
    if servico._status_atual == "aguardando_login":
        return True
    if _pausar_apos_etapa_segura(servico, "Ciclo pausado após tarefa segura."):
        return True
    return tarefas_processadas > 0 and servico._ha_mais_tarefas_pendentes()


def _finalizar_iteracao(servico) -> None:
    servico._processar_iteracao()
    if _pausar_apos_etapa_segura(servico, "Ciclo pausado após etapa segura."):
        return
    servico._set_status("dormindo", "Iteração concluída. Aguardando próximo ciclo.")


def _pausar_apos_etapa_segura(servico, mensagem: str) -> bool:
    if not servico._deve_pausar_por_comando():
        return False
    servico._pausar_ciclo("interrompido", mensagem)
    return True


def _tratar_estado_dormindo(servico, _comando: str, tempo_dormir: int, _te: int, _tc: int) -> bool:
    if servico._aguardar_ou_pausar(tempo_dormir):
        return True
    if not servico._stop_event.is_set():
        servico._set_status("executando", "Retomando execução.")
    return True


def _tratar_estado_erro(servico, comando: str, _td: int, tempo_erro: int, tempo_curto: int) -> bool:
    if comando != "iniciar":
        _aguardar_curto(servico, tempo_curto)
        return True
    servico._stop_event.wait(timeout=tempo_erro)
    if not servico._stop_event.is_set():
        servico._set_status("executando", "Tentando recuperação após erro.")
    return True


def _tratar_estado_parando(servico, _comando: str, _td: int, _te: int, _tc: int) -> bool:
    servico._pausar_ciclo("interrompido", "Ciclo pausado.")
    return True


def _aguardar_curto(servico, tempo_curto: int) -> None:
    servico._stop_event.wait(timeout=tempo_curto)


def _aguardar_estado_desconhecido(servico, status_db: str, tempo_curto: int) -> None:
    aviso(f"Estado desconhecido no banco: {status_db}")
    _aguardar_curto(servico, tempo_curto)
