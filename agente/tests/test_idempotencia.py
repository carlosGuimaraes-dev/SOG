import sqlite3
from contextlib import contextmanager
from pathlib import Path

import pytest

from banco import db
import pipeline


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
    monkeypatch.setattr(db, "get_conn", _get_conn)
    yield conn
    conn.close()


class FakePje:
    def __init__(self, numero):
        self.numero = numero
        self.coletas = 0

    def coletar_lista_processos(self):
        return [self.numero]

    def coletar_documentos(self, numero):
        self.coletas += 1
        return (
            [
                {
                    "doc_id": "doc-1",
                    "tipo": "Petição",
                    "data_assinatura": "2024-01-01",
                    "nome": "Petição inicial",
                }
            ],
            {"doc-1": "texto"},
        )

    def baixar_documento_pdf(self, doc_id, caminho):
        return False


class FakeSistj:
    def __init__(self):
        self.preenchimentos = 0

    def login(self):
        return True

    def preencher(self, payload, numero):
        self.preenchimentos += 1
        return {"screenshot_path": f"/tmp/{numero}.png"}


@pytest.fixture
def pipeline_sem_integracoes(monkeypatch):
    monkeypatch.setattr(
        pipeline,
        "datajud_consultar",
        lambda numero_sem_mascara: {
            "classe": "Procedimento Comum Cível",
            "valor_causa": "100,00",
            "data_distribuicao": "2024-01-01",
            "polo_ativo": "Autor",
        },
    )
    monkeypatch.setattr(
        pipeline,
        "processar_documentos",
        lambda docs, textos, custas_iniciais=None: {
            "sucumbente_nome": "Réu",
            "sucumbente_cpf_cnpj": "00000000000",
            "sucumbente_tipo": "Requerido",
            "honorarios_percentual": "100",
        },
    )
    monkeypatch.setattr(pipeline, "detectar_area", lambda classe, feito: "civel")
    monkeypatch.setattr(pipeline, "obter_regras_outros_itens", lambda area: [{"item_guia": "Custas"}])
    monkeypatch.setattr(pipeline, "enviar_alerta", lambda pendentes: None)


def test_writes_sensiveis_sao_idempotentes_no_banco(mock_db):
    processo_id = db.inserir_processo(
        "0000001-00.0000.0.00.0000",
        "000000100000000000000",
    )

    primeiro_dados_id = db.salvar_dados_processo(processo_id, {"classe": "Classe A"})
    segundo_dados_id = db.salvar_dados_processo(processo_id, {"classe": "Classe B"})
    primeiro_doc_id = db.salvar_documento(processo_id, "doc-1", "Petição", "2024-01-01", "A")
    segundo_doc_id = db.salvar_documento(processo_id, "doc-1", "Guia", "2024-01-02", "B")
    primeiro_log_id = db.registrar_log(processo_id, "pipeline", "erro", "falha critica")
    segundo_log_id = db.registrar_log(processo_id, "pipeline", "erro", "falha critica")

    with db.get_conn() as conn:
        dados = conn.execute("SELECT * FROM dados_processo").fetchall()
        docs = conn.execute("SELECT * FROM documentos_pje").fetchall()
        logs = conn.execute("SELECT * FROM log_execucao").fetchall()

    assert primeiro_dados_id == segundo_dados_id
    assert primeiro_doc_id == segundo_doc_id
    assert primeiro_log_id == segundo_log_id
    assert len(dados) == 1
    assert dados[0]["classe"] == "Classe B"
    assert len(docs) == 1
    assert docs[0]["tipo"] == "Guia"
    assert docs[0]["nome"] == "B"
    assert len(logs) == 1


def test_rerun_normal_nao_duplica_processo_dados_documentos_ou_logs(
    mock_db,
    pipeline_sem_integracoes,
):
    numero = "0000002-00.0000.0.00.0000"
    pje = FakePje(numero)
    sistj = FakeSistj()

    pipeline.rodar_pipeline(pje, sistj)
    pipeline.rodar_pipeline(pje, sistj)
    pipeline.rodar_pipeline(pje, sistj)

    with db.get_conn() as conn:
        assert conn.execute("SELECT COUNT(*) FROM processos").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM dados_processo").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM documentos_pje").fetchone()[0] == 1
        assert conn.execute(
            "SELECT COUNT(*) FROM log_execucao WHERE etapa = 'inicio'"
        ).fetchone()[0] == 1
        assert conn.execute(
            "SELECT COUNT(*) FROM log_execucao WHERE mensagem = 'Skip idempotente: status aguardando_aprovacao já tratado'"
        ).fetchone()[0] == 1

    assert pje.coletas == 1
    assert sistj.preenchimentos == 1


def test_reprocessamento_rearmado_roda_uma_vez_e_consumo_nao_e_reusado(
    mock_db,
    pipeline_sem_integracoes,
):
    numero = "0000003-00.0000.0.00.0000"
    processo_id = db.inserir_processo(numero, "000000300000000000000")
    db.salvar_dados_processo(processo_id, {"classe": "Classe antiga"})
    db.atualizar_status(processo_id, "rejeitado")
    db.solicitar_reprocessamento(processo_id, "operador", "ajustar")

    ciclo = db.criar_ciclo_agente()
    db.fechar_snapshot_ciclo(ciclo["uuid"], [])

    pje = FakePje(numero)
    sistj = FakeSistj()
    pipeline.rodar_pipeline(pje, sistj, ciclo_uuid=ciclo["uuid"])
    pipeline.rodar_pipeline(pje, sistj, ciclo_uuid=ciclo["uuid"])

    processo = db.obter_processo(processo_id)
    membro = db.listar_membros_ciclo(ciclo["uuid"])[0]
    with db.get_conn() as conn:
        total_dados = conn.execute("SELECT COUNT(*) FROM dados_processo").fetchone()[0]
        total_docs = conn.execute("SELECT COUNT(*) FROM documentos_pje").fetchone()[0]
        total_consumos = conn.execute(
            """
            SELECT COUNT(*)
            FROM log_execucao
            WHERE etapa = 'reprocessamento'
              AND mensagem = 'Reprocessamento rearmado consumido no ciclo'
            """
        ).fetchone()[0]

    assert processo["status"] == "aguardando_aprovacao"
    assert processo["reprocessar_solicitado_em"] is None
    assert membro["origem"] == "rearmado"
    assert membro["processado_em"] is not None
    assert total_dados == 1
    assert total_docs == 1
    assert total_consumos == 1
    assert pje.coletas == 1
    assert sistj.preenchimentos == 1
