from sog_shared import db


def test_status_sem_registro_orienta_runtime_compose(client, auth_headers):
    resp = client.get("/api/v1/agente/status", headers=auth_headers)

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "desconhecido"
    assert "Docker Compose" in data["mensagem"]
    assert "desktop" not in data["mensagem"].lower()
    assert data["online"] is False


def test_iniciar_rejeita_ciclo_concorrente(client, auth_headers):
    db.criar_ou_atualizar_controle_agente(
        comando="iniciar",
        status="executando",
        ciclo_uuid="ciclo-ativo",
        ciclo_snapshot='{"lote": [1]}',
    )

    resp = client.post("/api/v1/agente/iniciar", headers=auth_headers)

    assert resp.status_code == 409
    assert resp.json()["detail"] == "Já existe um ciclo do agente em execução."
    controle = db.obter_controle_agente()
    assert controle["ciclo_uuid"] == "ciclo-ativo"
    assert controle["ciclo_snapshot"] == '{"lote": [1]}'


def test_parar_preserva_uuid_snapshot_e_deixa_retomavel(client, auth_headers):
    db.criar_ou_atualizar_controle_agente(
        comando="iniciar",
        status="executando",
        ciclo_uuid="ciclo-123",
        ciclo_snapshot='{"processos": ["0001"]}',
    )

    resp = client.post("/api/v1/agente/parar", headers=auth_headers)

    assert resp.status_code == 200
    controle = db.obter_controle_agente()
    assert controle["status"] == "parando"
    assert controle["comando"] == "parar"
    assert controle["ciclo_uuid"] == "ciclo-123"
    assert controle["ciclo_snapshot"] == '{"processos": ["0001"]}'
    assert controle["pausado_em"] is not None


def test_iniciar_retoma_ciclo_pausado_sem_trocar_uuid(client, auth_headers):
    db.criar_ou_atualizar_controle_agente(
        comando="parar",
        status="interrompido",
        ciclo_uuid="ciclo-retomavel",
        ciclo_snapshot='{"offset": 2}',
        pausado_em="2026-05-30T00:00:00+00:00",
    )

    resp = client.post("/api/v1/agente/iniciar", headers=auth_headers)

    assert resp.status_code == 200
    data = resp.json()
    assert data["resumed"] is True
    assert data["ciclo_uuid"] == "ciclo-retomavel"
    controle = db.obter_controle_agente()
    assert controle["status"] == "iniciando"
    assert controle["comando"] == "iniciar"
    assert controle["ciclo_uuid"] == "ciclo-retomavel"
    assert controle["ciclo_snapshot"] == '{"offset": 2}'
    assert controle["retomado_em"] is not None


def test_status_expoe_relogin_required_e_bloqueios(client, auth_headers):
    db.criar_ou_atualizar_controle_agente(
        comando="parar",
        status="aguardando_login",
        mensagem="Sessão pje expirada.",
        ciclo_uuid="ciclo-login",
        ciclo_snapshot='{"ultima_etapa": "pje"}',
    )

    resp = client.get("/api/v1/agente/status", headers=auth_headers)

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "aguardando_login"
    assert data["relogin_required"] is True
    assert data["pode_iniciar"] is True
    assert data["pode_parar"] is False
    assert data["ciclo_uuid"] == "ciclo-login"
    assert data["ciclo_snapshot"] == '{"ultima_etapa": "pje"}'
