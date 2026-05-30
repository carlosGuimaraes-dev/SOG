"""
Testes do loop de processamento de tarefas do serviço longo.
"""
import threading
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from modulos.auth_manager import ReautenticacaoNecessariaError
from servico import AgenteServico
from sog_shared import db


SCHEMA_SQL = Path(__file__).parent.parent / "src" / "banco" / "schema.sql"


@pytest.fixture
def mock_db(monkeypatch):
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_SQL.read_text(encoding="utf-8"))
    conn.commit()

    @contextmanager
    def _get_conn():
        yield conn

    monkeypatch.setattr("sog_shared.db.get_conn", _get_conn)
    yield conn
    conn.close()


def _servico_fake() -> AgenteServico:
    servico = AgenteServico.__new__(AgenteServico)
    servico._locks = {"pje": False, "sistj": False}
    servico.pje = MagicMock()
    servico.sistj = MagicMock()
    servico._set_status = MagicMock()
    servico._pausar_ciclo = MagicMock()
    servico._stop_event = threading.Event()
    servico._ler_comando = MagicMock(return_value=("iniciar", "executando"))
    servico._ciclo_uuid = None
    servico._tarefas_por_iteracao = 3
    return servico


def test_processa_cinco_tarefas_sequencialmente_sem_deadlock():
    servico = _servico_fake()
    tarefas = [
        {"id": idx, "tipo": "dummy", "sistema_alvo": "pje", "payload": {}}
        for idx in range(1, 6)
    ]

    with patch("servico.proxima_tarefa_pendente", side_effect=tarefas + [None]), \
         patch("servico.executar_tarefa", return_value={"ok": True}) as executar_mock, \
         patch("servico.concluir_tarefa", return_value=True) as concluir_mock, \
         patch("servico.devolver_tarefa_pendente") as devolver_mock:
        processadas = servico._processar_tarefas_pendentes(max_tarefas=5)

    assert processadas == 5
    assert executar_mock.call_count == 5
    assert concluir_mock.call_count == 5
    assert devolver_mock.call_count == 0
    assert servico._locks == {"pje": False, "sistj": False}


def test_cancelamento_durante_execucao_nao_prende_lock():
    servico = _servico_fake()
    tarefa = {"id": 1, "tipo": "dummy", "sistema_alvo": "pje", "payload": {}}

    with patch("servico.proxima_tarefa_pendente", side_effect=[tarefa, None]), \
         patch("servico.executar_tarefa", return_value={"ok": True}), \
         patch("servico.concluir_tarefa", return_value=False) as concluir_mock:
        processadas = servico._processar_tarefas_pendentes(max_tarefas=1)

    assert processadas == 1
    concluir_mock.assert_called_once_with(1, "concluido", resultado={"ok": True})
    assert servico._locks == {"pje": False, "sistj": False}


def test_comando_parar_interrompe_antes_da_proxima_tarefa_segura():
    servico = _servico_fake()
    servico._ler_comando = MagicMock(
        side_effect=[("iniciar", "executando"), ("parar", "executando")]
    )
    tarefas = [
        {"id": 1, "tipo": "dummy", "sistema_alvo": "pje", "payload": {}},
        {"id": 2, "tipo": "dummy", "sistema_alvo": "pje", "payload": {}},
    ]

    with patch("servico.proxima_tarefa_pendente", side_effect=tarefas), \
         patch("servico.executar_tarefa", return_value={"ok": True}) as executar_mock, \
         patch("servico.concluir_tarefa", return_value=True):
        processadas = servico._processar_tarefas_pendentes(max_tarefas=2)

    assert processadas == 1
    assert executar_mock.call_count == 1
    assert servico._locks == {"pje": False, "sistj": False}


def test_expiracao_sessao_devolve_tarefa_e_pausa_para_relogin():
    servico = _servico_fake()
    tarefa = {"id": 1, "tipo": "dummy", "sistema_alvo": "pje", "payload": {}}

    with patch("servico.proxima_tarefa_pendente", return_value=tarefa), \
         patch("servico.executar_tarefa", side_effect=ReautenticacaoNecessariaError("pje")), \
         patch("servico.concluir_tarefa") as concluir_mock, \
         patch("servico.devolver_tarefa_pendente") as devolver_mock:
        processadas = servico._processar_tarefas_pendentes(max_tarefas=1)

    assert processadas == 1
    devolver_mock.assert_called_once_with(1)
    concluir_mock.assert_not_called()
    servico._pausar_ciclo.assert_called_once_with(
        "aguardando_login",
        "Sessão pje expirada durante tarefa.",
    )
    assert servico._locks == {"pje": False, "sistj": False}


def test_inicio_servico_preserva_ciclo_interrompido_retomavel(mock_db):
    db.criar_ou_atualizar_controle_agente(
        comando="parar",
        status="interrompido",
        mensagem="Ciclo pausado.",
        ciclo_uuid="ciclo-retomavel",
        ciclo_snapshot='{"offset": 2}',
    )
    servico = _servico_fake()
    servico._pausar_ciclo = AgenteServico._pausar_ciclo.__get__(servico, AgenteServico)

    servico._registrar_inicio_servico()

    controle = db.obter_controle_agente()
    assert controle["status"] == "interrompido"
    assert controle["comando"] == "parar"
    assert controle["ciclo_uuid"] == "ciclo-retomavel"
    assert controle["ciclo_snapshot"] == '{"offset": 2}'
    assert servico._status_atual == "interrompido"


def test_inicio_servico_pausa_ciclo_ativo_orfao_sem_trocar_uuid(mock_db):
    db.criar_ou_atualizar_controle_agente(
        comando="iniciar",
        status="executando",
        ciclo_uuid="ciclo-ativo",
        ciclo_snapshot='{"offset": 1}',
    )
    servico = _servico_fake()
    servico._pausar_ciclo = AgenteServico._pausar_ciclo.__get__(servico, AgenteServico)

    servico._registrar_inicio_servico()

    controle = db.obter_controle_agente()
    assert controle["status"] == "erro_pausado"
    assert controle["comando"] == "parar"
    assert controle["ciclo_uuid"] == "ciclo-ativo"
    assert controle["ciclo_snapshot"] == '{"offset": 1}'
    assert controle["pausado_em"] is not None

def test_pausa_para_relogin_dispara_notificacao(mock_db):
    servico = _servico_fake()
    servico._pausar_ciclo = AgenteServico._pausar_ciclo.__get__(servico, AgenteServico)

    with patch("servico.notificar_relogin_required") as notificar_mock, \
         patch("servico.notificar_erro_fatal") as fatal_mock:
        servico._pausar_ciclo("aguardando_login", "Sessão expirada.")

    controle = db.obter_controle_agente()
    assert controle["status"] == "aguardando_login"
    notificar_mock.assert_called_once_with()
    fatal_mock.assert_not_called()


def test_pausa_por_erro_fatal_dispara_notificacao(mock_db):
    servico = _servico_fake()
    servico._pausar_ciclo = AgenteServico._pausar_ciclo.__get__(servico, AgenteServico)

    with patch("servico.notificar_relogin_required") as relogin_mock, \
         patch("servico.notificar_erro_fatal") as fatal_mock:
        servico._pausar_ciclo("erro_pausado", "Erro interno com dado sensível 0701234.")

    controle = db.obter_controle_agente()
    assert controle["status"] == "erro_pausado"
    relogin_mock.assert_not_called()
    fatal_mock.assert_called_once_with()


def test_finalizacao_de_ciclo_dispara_resumo_agregado():
    servico = _servico_fake()
    servico._ciclo_uuid = "ciclo-1"
    membros = [
        {"numero": "0701234-56.2024.8.07.0001", "status_atual": "emitido"},
        {"numero": "0711111-22.2024.8.07.0001", "status_atual": "erro"},
    ]

    with patch("servico.rodar_pipeline") as pipeline_mock, \
         patch("servico.emitir_pendentes") as emitir_mock, \
         patch("servico.listar_membros_ciclo", return_value=membros), \
         patch("servico.finalizar_ciclo") as finalizar_mock, \
         patch("servico.obter_ciclo", return_value={"uuid": "ciclo-1"}), \
         patch("servico.notificar_ciclo_concluido") as notificar_mock:
        servico._processar_iteracao()

    pipeline_mock.assert_called_once()
    emitir_mock.assert_called_once()
    finalizar_mock.assert_called_once_with("ciclo-1")
    notificar_mock.assert_called_once_with({"uuid": "ciclo-1"}, membros)
    assert servico._ciclo_uuid is None


def test_relogin_retoma_mesmo_ciclo_aguardando_login(mock_db):
    mock_db.execute(
        """
        INSERT INTO agente_ciclos (uuid, rotulo, status, fechado_em)
        VALUES ('ciclo-login', 'Ciclo login', 'aguardando_login', CURRENT_TIMESTAMP)
        """
    )
    mock_db.commit()
    db.criar_ou_atualizar_controle_agente(
        comando="iniciar",
        status="aguardando_login",
        mensagem="Sessão expirada.",
        ciclo_uuid="ciclo-login",
        ciclo_snapshot='{"offset": 3}',
    )
    servico = _servico_fake()
    servico._ler_comando = MagicMock(return_value=("iniciar", "aguardando_login"))
    servico._set_status = AgenteServico._set_status.__get__(servico, AgenteServico)
    servico._pausar_ciclo = AgenteServico._pausar_ciclo.__get__(servico, AgenteServico)
    servico._autenticar_interativo = MagicMock(return_value=True)

    servico._loop_iteration()

    controle = db.obter_controle_agente()
    assert controle["status"] == "executando"
    assert controle["ciclo_uuid"] == "ciclo-login"
    assert controle["ciclo_snapshot"] == '{"offset": 3}'
    assert servico._ciclo_uuid == "ciclo-login"
