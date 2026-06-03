import sqlite3
import sys
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))

from banco import db
from modulos.emissor import emitir_e_anexar
from modulos.executor_tarefas import _anexar_demonstrativo_pje
from sog_shared.infra_db import SCHEMA_PATH


@contextmanager
def _conn_context(conn):
    yield conn


def _configurar_db_memoria(monkeypatch):
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    conn.commit()
    monkeypatch.setattr("sog_shared.infra_db.get_conn", lambda: _conn_context(conn))
    monkeypatch.setattr("sog_shared.db.get_conn", lambda: _conn_context(conn))
    monkeypatch.setattr(db, "get_conn", lambda: _conn_context(conn))
    return conn


class FakeSistj:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.aprovacoes = 0

    def garantir_autenticado(self):
        return True

    def gravar_e_aprovar(self, numero_sem_mascara):
        self.aprovacoes += 1
        return self.pdf_path


class FakePje:
    def __init__(self, resultados):
        self.resultados = list(resultados)
        self.anexos = []

    def garantir_autenticado(self):
        return True

    def anexar_demonstrativo(self, numero, caminho_pdf):
        self.anexos.append((numero, caminho_pdf))
        return self.resultados.pop(0)


def test_emitir_e_anexar_reaproveita_demonstrativo_apos_sucesso_parcial(monkeypatch, tmp_path):
    conn = _configurar_db_memoria(monkeypatch)
    numero = "0000004-00.0000.0.00.0000"
    numero_sem_mascara = "000000400000000000000"
    ciclo = db.criar_ciclo_agente()
    db.fechar_snapshot_ciclo(ciclo["uuid"], [numero])
    processo_id = db.processo_existe(numero)["id"]
    db.salvar_dados_processo(processo_id, {"classe": "Classe A"})
    db.atualizar_status(processo_id, "aprovado")

    pdf_path = tmp_path / f"{numero_sem_mascara}.pdf"
    pdf_path.write_bytes(b"pdf")

    sistj = FakeSistj(str(pdf_path))
    pje = FakePje([False, True])

    assert emitir_e_anexar(processo_id, sistj, pje) is False
    assert emitir_e_anexar(processo_id, sistj, pje) is True

    evidencia_pdf = db.obter_evidencia_emissao(
        processo_id,
        db.ETAPA_EVIDENCIA_DEMONSTRATIVO_SISTJ,
    )
    evidencia_anexo = db.obter_evidencia_emissao(
        processo_id,
        db.ETAPA_EVIDENCIA_ANEXO_PJE,
    )
    processo = db.obter_processo(processo_id)

    assert sistj.aprovacoes == 1
    assert len(pje.anexos) == 2
    assert evidencia_pdf["referencia_arquivo"] == str(pdf_path)
    assert evidencia_anexo["referencia_arquivo"] == str(pdf_path)
    assert processo["status"] == "emitido"
    assert db.obter_ciclo(ciclo["uuid"])["total_concluidos"] == 1

    conn.close()


def test_anexar_demonstrativo_pje_reusa_evidencia_do_pdf_emitido(monkeypatch, tmp_path):
    conn = _configurar_db_memoria(monkeypatch)
    numero = "0000005-00.0000.0.00.0000"
    numero_sem_mascara = "000000500000000000000"
    ciclo = db.criar_ciclo_agente()
    db.fechar_snapshot_ciclo(ciclo["uuid"], [numero])
    processo_id = db.processo_existe(numero)["id"]
    db.salvar_dados_processo(processo_id, {"classe": "Classe A"})
    db.atualizar_status(processo_id, "aprovado")

    pdf_path = tmp_path / "emitido.pdf"
    pdf_path.write_bytes(b"pdf")
    db.salvar_evidencia_emissao(
        processo_id,
        db.ETAPA_EVIDENCIA_DEMONSTRATIVO_SISTJ,
        referencia_arquivo=str(pdf_path),
        referencia_externa=numero_sem_mascara,
    )

    pje = FakePje([True])
    resultado = _anexar_demonstrativo_pje({"processo_id": processo_id}, pje, None)

    evidencia_anexo = db.obter_evidencia_emissao(
        processo_id,
        db.ETAPA_EVIDENCIA_ANEXO_PJE,
    )
    processo = db.obter_processo(processo_id)

    assert resultado["sucesso"] is True
    assert pje.anexos == [(numero, str(pdf_path))]
    assert evidencia_anexo["referencia_arquivo"] == str(pdf_path)
    assert processo["status"] == "emitido"
    assert db.obter_ciclo(ciclo["uuid"])["total_concluidos"] == 1

    conn.close()


def test_emitir_e_anexar_incrementa_erro_no_ciclo_do_processo(monkeypatch, tmp_path):
    conn = _configurar_db_memoria(monkeypatch)
    numero = "0000006-00.0000.0.00.0000"
    numero_sem_mascara = "000000600000000000000"
    ciclo = db.criar_ciclo_agente()
    db.fechar_snapshot_ciclo(ciclo["uuid"], [numero])
    processo_id = db.processo_existe(numero)["id"]
    db.salvar_dados_processo(processo_id, {"classe": "Classe A"})
    db.atualizar_status(processo_id, "aprovado")

    pdf_path = tmp_path / f"{numero_sem_mascara}.pdf"
    pdf_path.write_bytes(b"pdf")

    sistj = FakeSistj(str(pdf_path))
    pje = FakePje([False])

    assert emitir_e_anexar(processo_id, sistj, pje) is False

    processo = db.obter_processo(processo_id)
    ciclo_atualizado = db.obter_ciclo(ciclo["uuid"])

    assert processo["status"] == "erro"
    assert ciclo_atualizado["total_concluidos"] == 0
    assert ciclo_atualizado["total_erros"] == 1

    conn.close()
