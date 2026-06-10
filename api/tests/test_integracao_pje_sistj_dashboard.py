"""
Testes das rotas de integração PJe/SISTJWEB e dashboard.
"""

from sog_shared import db


def test_enfileirar_tarefa_pje_consultar_etiqueta(client, auth_headers):
    resp = client.post("/api/v1/pje/consultar-etiqueta", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["tipo"] == "consultar_etiqueta_pje"
    assert data["status"] == "pendente"
    assert data["sistema_alvo"] == "pje"


def test_enfileirar_tarefa_sistj_preencher(client, auth_headers):
    resp = client.post("/api/v1/sistj/preencher/123", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["tipo"] == "preencher_sistj"
    assert data["payload"]["processo_id"] == 123
    assert data["sistema_alvo"] == "sistj"


def test_sessao_pje_reflete_ultima_verificacao_concluida(client, auth_headers, mock_db):
    task_id = db.criar_tarefa(
        tipo="verificar_sessao_pje",
        payload={},
        sistema_alvo="pje",
        criado_por="admin",
    )
    db.concluir_tarefa(task_id, "concluido", resultado={"logado": True})

    resp = client.get("/api/v1/pje/sessao", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["sistema"] == "pje"
    assert data["logado"] is True
    assert data["mensagem"] == "Sessão ativa"


def test_dashboard_sessoes_consolida_estado(client, auth_headers, mock_db):
    pje_id = db.criar_tarefa(
        tipo="verificar_sessao_pje",
        payload={},
        sistema_alvo="pje",
        criado_por="admin",
    )
    db.concluir_tarefa(pje_id, "concluido", resultado={"logado": True})

    sistj_id = db.criar_tarefa(
        tipo="verificar_sessao_sistj",
        payload={},
        sistema_alvo="sistj",
        criado_por="admin",
    )
    db.concluir_tarefa(sistj_id, "concluido", resultado={"logado": False})

    resp = client.get("/api/v1/dashboard/sessoes", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["pje"]["logado"] is True
    assert data["pje"]["mensagem"] == "Sessão ativa"
    assert data["sistj"]["logado"] is False
    assert data["sistj"]["mensagem"] == "Aguardando login"
    assert data["tarefas_pendentes"] == 0
    assert data["tarefas_executando"] == 0


def test_dashboard_reenfileira_tarefa_stale(client, auth_headers, mock_db):
    task_id = db.criar_tarefa(
        tipo="verificar_sessao_pje",
        payload={},
        sistema_alvo="pje",
        criado_por="admin",
    )
    mock_db.execute(
        """
        UPDATE agente_tarefas
           SET status = 'executando',
               iniciado_em = datetime('now', '-10 minutes')
         WHERE id = ?
        """,
        (task_id,),
    )
    mock_db.commit()

    resp = client.get("/api/v1/dashboard/sessoes", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["tarefas_pendentes"] == 1
    assert data["tarefas_executando"] == 0
