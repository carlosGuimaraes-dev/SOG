import uuid


def test_iniciar_agente_cria_ciclo_persistido(client, mock_db, auth_headers):
    resp = client.post("/api/v1/agente/iniciar", headers=auth_headers)

    assert resp.status_code == 200
    data = resp.json()
    ciclo_uuid = data["ciclo_uuid"]
    uuid.UUID(ciclo_uuid)

    from sog_shared import db

    ciclo = db.obter_ciclo(ciclo_uuid)
    assert ciclo is not None
    assert ciclo["uuid"] == ciclo_uuid
    assert ciclo["rotulo"].startswith("Ciclo ")
    assert ciclo["status"] == "iniciando"


def test_snapshot_fechado_inclui_novos_e_rearmados_sem_reativar_conhecidos(
    client,
    mock_db,
    auth_headers,
):
    from sog_shared import db

    rearmado_id = db.inserir_processo(
        "0000002-00.0000.0.00.0000", "000000200000000000000"
    )
    rearmado_fora_pje_id = db.inserir_processo(
        "0000006-00.0000.0.00.0000", "000000600000000000000"
    )
    conhecido_id = db.inserir_processo(
        "0000003-00.0000.0.00.0000", "000000300000000000000"
    )
    erro_id = db.inserir_processo(
        "0000004-00.0000.0.00.0000", "000000400000000000000"
    )
    db.atualizar_status(conhecido_id, "aguardando_aprovacao")
    db.atualizar_status(erro_id, "erro", "Falha anterior")

    ciclo = db.criar_ciclo_agente()
    fechado = db.fechar_snapshot_ciclo(
        ciclo["uuid"],
        [
            "0000001-00.0000.0.00.0000",
            "0000002-00.0000.0.00.0000",
            "0000003-00.0000.0.00.0000",
            "0000004-00.0000.0.00.0000",
        ],
    )

    assert fechado["status"] == "executando"
    assert fechado["total_membros"] == 3
    assert fechado["total_novos"] == 1
    assert fechado["total_rearmados"] == 2

    membros = db.listar_membros_ciclo(ciclo["uuid"])
    assert {m["numero"] for m in membros} == {
        "0000001-00.0000.0.00.0000",
        "0000002-00.0000.0.00.0000",
        "0000006-00.0000.0.00.0000",
    }
    assert {m["origem"] for m in membros} == {"novo_pje", "rearmado"}
    assert all(m["processo_id"] != conhecido_id for m in membros)
    assert all(m["processo_id"] != erro_id for m in membros)
    assert any(m["processo_id"] == rearmado_id for m in membros)
    assert any(m["processo_id"] == rearmado_fora_pje_id for m in membros)

    db.inserir_processo("0000005-00.0000.0.00.0000", "000000500000000000000")
    reaberto = db.fechar_snapshot_ciclo(
        ciclo["uuid"],
        ["0000005-00.0000.0.00.0000"],
    )
    assert reaberto["total_membros"] == 3

    detalhe = client.get(
        f"/api/v1/agente/ciclos/{ciclo['uuid']}",
        headers=auth_headers,
    )
    assert detalhe.status_code == 200
    data = detalhe.json()
    assert data["uuid"] == ciclo["uuid"]
    assert [m["numero"] for m in data["membros"]] == [
        "0000002-00.0000.0.00.0000",
        "0000006-00.0000.0.00.0000",
        "0000001-00.0000.0.00.0000",
    ]
