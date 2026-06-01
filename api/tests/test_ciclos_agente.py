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


def test_snapshot_fechado_inclui_novos_e_rearmados_explicitos_uma_vez(
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
    pendente_sem_marcacao_id = db.inserir_processo(
        "0000004-00.0000.0.00.0000", "000000400000000000000"
    )
    db.atualizar_status(rearmado_id, "erro", "Falha anterior")
    db.atualizar_status(rearmado_fora_pje_id, "rejeitado")
    db.atualizar_status(conhecido_id, "aguardando_aprovacao")
    db.solicitar_reprocessamento(rearmado_id, "operador", "nova tentativa")
    db.solicitar_reprocessamento(rearmado_fora_pje_id, "operador", "")

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
    assert all(m["processo_id"] != pendente_sem_marcacao_id for m in membros)
    assert any(m["processo_id"] == rearmado_id for m in membros)
    assert any(m["processo_id"] == rearmado_fora_pje_id for m in membros)
    assert all(
        m["status_snapshot"] in {"erro", "rejeitado", "pendente"} for m in membros
    )

    with db.get_conn() as conn:
        consumidos = conn.execute(
            """
            SELECT id, reprocessar_solicitado_em
            FROM processos
            WHERE id IN (?, ?)
            """,
            (rearmado_id, rearmado_fora_pje_id),
        ).fetchall()
    assert all(row["reprocessar_solicitado_em"] is None for row in consumidos)

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

    db.finalizar_ciclo(ciclo["uuid"])
    novo_ciclo = db.criar_ciclo_agente()
    segundo_fechado = db.fechar_snapshot_ciclo(novo_ciclo["uuid"], [])
    assert segundo_fechado["total_rearmados"] == 0


def test_aprovar_processo_recalcula_contadores_do_ciclo_atual(
    client,
    mock_db,
    auth_headers,
):
    from sog_shared import db

    numero = "0000007-00.0000.0.00.0000"
    ciclo = db.criar_ciclo_agente()
    db.fechar_snapshot_ciclo(ciclo["uuid"], [numero])
    processo_id = db.processo_existe(numero)["id"]
    db.atualizar_status(processo_id, "aguardando_aprovacao")

    antes = db.obter_ciclo(ciclo["uuid"])
    assert antes["total_concluidos"] == 0

    resp = client.post(f"/api/v1/aprovar/{processo_id}", headers=auth_headers)

    assert resp.status_code == 200
    depois = db.obter_ciclo(ciclo["uuid"])
    assert depois["total_concluidos"] == 1
    assert depois["total_erros"] == 0
