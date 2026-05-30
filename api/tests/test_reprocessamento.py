import pytest


@pytest.mark.parametrize("status", ["erro", "pendente_manual", "rejeitado"])
def test_reprocessar_marca_processo_e_registra_auditoria_sem_tarefa(
    client,
    auth_headers,
    status,
):
    from sog_shared import db

    processo_id = db.inserir_processo(
        f"00000{len(status)}1-00.0000.0.00.0000",
        f"00000{len(status)}10000000000000",
    )
    db.atualizar_status(processo_id, status, "Falha anterior")

    resp = client.post(
        f"/api/v1/processos/{processo_id}/reprocessar",
        json={"motivo": "conferir novamente"},
        headers=auth_headers,
    )

    assert resp.status_code == 200
    assert resp.json()["message"] == "Reprocessamento solicitado para o próximo ciclo."

    with db.get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM processos WHERE id = ?", (processo_id,)
        ).fetchone()
        logs = conn.execute(
            "SELECT * FROM log_execucao WHERE processo_id = ?", (processo_id,)
        ).fetchall()

    assert row["status"] == status
    assert row["reprocessar_solicitado_em"] is not None
    assert row["reprocessar_solicitado_por"] == "admin"
    assert row["reprocessar_motivo"] == "conferir novamente"
    assert len(logs) == 1
    assert logs[0]["etapa"] == "reprocessamento"
    assert "admin" in logs[0]["mensagem"]
    assert "conferir novamente" in logs[0]["mensagem"]
    total_tarefas, tarefas = db.listar_tarefas()
    assert total_tarefas == 0
    assert tarefas == []


def test_reprocessar_rejeita_status_nao_elegivel(client, auth_headers):
    from sog_shared import db

    processo_id = db.inserir_processo(
        "1000001-00.0000.0.00.0000",
        "100000100000000000000",
    )
    db.atualizar_status(processo_id, "aprovado")

    resp = client.post(
        f"/api/v1/processos/{processo_id}/reprocessar",
        json={"motivo": "fora de estado"},
        headers=auth_headers,
    )

    assert resp.status_code == 409
    with db.get_conn() as conn:
        row = conn.execute(
            "SELECT reprocessar_solicitado_em FROM processos WHERE id = ?",
            (processo_id,),
        ).fetchone()
    assert row["reprocessar_solicitado_em"] is None


def test_reprocessar_retorna_404_para_processo_inexistente(client, auth_headers):
    resp = client.post(
        "/api/v1/processos/999/reprocessar",
        json={"motivo": "nao existe"},
        headers=auth_headers,
    )

    assert resp.status_code == 404
