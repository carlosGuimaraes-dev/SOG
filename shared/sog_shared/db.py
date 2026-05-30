"""
Módulo de acesso ao banco SQLite — versão compartilhada.

Sem side-effects no import. init_db() deve ser chamada explicitamente.
"""
import json
import os
import re
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

# DB_PATH pode vir de variável de ambiente ou do pacote shared config
from sog_shared.config import DB_PATH

SCHEMA_PATH = Path(__file__).parent / "schema.sql"

ESTADOS_CICLO_ATIVO = frozenset({
    "iniciando",
    "autenticando",
    "executando",
    "dormindo",
    "parando",
})
ESTADOS_CICLO_RETOMAVEL = frozenset({
    "pausado",
    "interrompido",
    "aguardando_login",
    "erro_pausado",
    "erro",
})
COLUNAS_AGENTE_CONTROLE = {
    "ciclo_uuid": "TEXT",
    "ciclo_snapshot": "TEXT DEFAULT '{}'",
    "pausado_em": "DATETIME",
    "retomado_em": "DATETIME",
}
COLUNAS_PROCESSOS = {
    "reprocessar_solicitado_em": "DATETIME",
    "reprocessar_solicitado_por": "TEXT",
    "reprocessar_motivo": "TEXT",
}
STATUS_REPROCESSAMENTO_EXPLICITO = frozenset({
    "erro",
    "pendente_manual",
    "rejeitado",
})

COLUNAS_PERMITIDAS_DADOS_PROCESSO = frozenset({
    "instancia",
    "processo_eletronico",
    "circunscricao",
    "competencia",
    "feito",
    "classe",
    "valor_causa",
    "valor_causa_atualizado",
    "data_distribuicao",
    "polo_ativo",
    "polo_passivo",
    "tipo_guia",
    "pro_rata",
    "sucumbentes",
    "ids_oficios",
    "ids_alvaras",
    "ids_traslados",
    "ids_mandados",
    "ids_cartas_sentenca",
    "ids_ar",
    "ids_armp",
    "ids_circunscricao_origem",
    "ids_outra_circunscricao",
    "outros_itens",
    "compensacao",
    "custas_pagas",
    "sucumbente_nome",
    "sucumbente_cpf_cnpj",
    "sucumbente_tipo",
    "honorarios_percentual",
    "suspensao_exigibilidade",
    "valor_total_recolher",
    "area_direito",
    "obs_operador",
    "screenshot_path",
})


def _setup_conn(conn: sqlite3.Connection) -> sqlite3.Connection:
    """Aplica PRAGMAs de concorrência e configura row_factory."""
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def init_db():
    """Inicializa o banco com o schema se ainda não existir.

    Deve ser chamada explicitamente no startup da aplicação.
    """
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30)
    try:
        _setup_conn(conn)
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        _garantir_colunas_processos(conn)
        _garantir_colunas_agente_controle(conn)
        conn.commit()
    finally:
        conn.close()


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    _setup_conn(conn)
    try:
        yield conn
    finally:
        conn.close()


# Processos ------------------------------------------------------------------

def processo_existe(numero: str) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, status FROM processos WHERE numero = ?", (numero,)
        ).fetchone()
        if row is None:
            return None
        return {"id": row["id"], "status": row["status"]}


def inserir_processo(numero: str, numero_sem_mascara: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO processos (numero, numero_sem_mascara) VALUES (?, ?)",
            (numero, numero_sem_mascara),
        )
        conn.commit()
        return cur.lastrowid


def atualizar_status(
    processo_id: int,
    status: str,
    erro_msg: Optional[str] = None,
    incrementar_tentativa: bool = False,
):
    with get_conn() as conn:
        if incrementar_tentativa:
            conn.execute(
                "UPDATE processos SET status = ?, erro_msg = ?, tentativas = tentativas + 1, atualizado_em = CURRENT_TIMESTAMP WHERE id = ?",
                (status, erro_msg, processo_id),
            )
        else:
            conn.execute(
                "UPDATE processos SET status = ?, erro_msg = ?, atualizado_em = CURRENT_TIMESTAMP WHERE id = ?",
                (status, erro_msg, processo_id),
            )
        conn.commit()


def solicitar_reprocessamento(
    processo_id: int,
    usuario: str,
    motivo: str = "",
) -> Dict[str, Any]:
    motivo_seguro = motivo.replace("\n", " ").replace("\r", "")[:500]
    with get_conn() as conn:
        try:
            conn.execute("BEGIN IMMEDIATE")
            _garantir_colunas_processos(conn)
            row = conn.execute(
                "SELECT * FROM processos WHERE id = ?", (processo_id,)
            ).fetchone()
            if row is None:
                conn.rollback()
                return {"accepted": False, "reason": "not_found"}
            if row["status"] not in STATUS_REPROCESSAMENTO_EXPLICITO:
                conn.rollback()
                return {
                    "accepted": False,
                    "reason": "status_not_allowed",
                    "status": row["status"],
                }

            conn.execute(
                """
                UPDATE processos
                   SET reprocessar_solicitado_em = CURRENT_TIMESTAMP,
                       reprocessar_solicitado_por = ?,
                       reprocessar_motivo = ?,
                       atualizado_em = CURRENT_TIMESTAMP
                 WHERE id = ?
                """,
                (usuario, motivo_seguro, processo_id),
            )
            detalhes = f"Reprocessamento solicitado por {usuario}"
            if motivo_seguro:
                detalhes = f"{detalhes}. Motivo: {motivo_seguro}"
            conn.execute(
                """
                INSERT INTO log_execucao (processo_id, etapa, status, mensagem)
                VALUES (?, 'reprocessamento', 'ok', ?)
                """,
                (processo_id, detalhes),
            )
            atualizado = conn.execute(
                "SELECT * FROM processos WHERE id = ?", (processo_id,)
            ).fetchone()
            conn.commit()
            return {"accepted": True, "processo": dict(atualizado)}
        except Exception:
            conn.rollback()
            raise


def listar_pendentes(limit: int = 1000, offset: int = 0) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM processos WHERE status IN ('pendente', 'erro') AND tentativas < 3 ORDER BY criado_em LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]


def listar_aguardando_aprovacao(limit: int = 1000, offset: int = 0) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM processos WHERE status = 'aguardando_aprovacao' ORDER BY atualizado_em DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]


def obter_processo(processo_id: int) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM processos WHERE id = ?", (processo_id,)
        ).fetchone()
        return dict(row) if row else None


# Dados processo -------------------------------------------------------------

def salvar_dados_processo(processo_id: int, dados: Dict[str, Any]) -> int:
    campos = list(dados.keys())
    invalidas = set(campos) - COLUNAS_PERMITIDAS_DADOS_PROCESSO
    if invalidas:
        raise ValueError(
            f"Colunas não permitidas em dados_processo: {sorted(invalidas)}"
        )

    valores = list(dados.values())
    # Converte listas/dicts para JSON strings
    for i, v in enumerate(valores):
        if isinstance(v, (list, dict)):
            valores[i] = json.dumps(v, ensure_ascii=False)

    placeholders = ", ".join(["?"] * len(campos))
    colunas = ", ".join(campos)

    with get_conn() as conn:
        cur = conn.execute(
            f"INSERT INTO dados_processo (processo_id, {colunas}) VALUES (?, {placeholders})",
            (processo_id, *valores),
        )
        conn.commit()
        return cur.lastrowid


def obter_dados_processo(processo_id: int) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM dados_processo WHERE processo_id = ? ORDER BY id DESC LIMIT 1",
            (processo_id,),
        ).fetchone()
        if not row:
            return None
        dados = dict(row)
        # Deserializa JSON
        for campo in ("sucumbentes", "outros_itens", "compensacao", "custas_pagas"):
            if dados.get(campo):
                try:
                    dados[campo] = json.loads(dados[campo])
                except json.JSONDecodeError:
                    pass
        return dados


# Documentos PJE -------------------------------------------------------------

def salvar_documento(
    processo_id: int, doc_id: str, tipo: str, data_assinatura: str, nome: str
):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO documentos_pje (processo_id, doc_id, tipo, data_assinatura, nome) VALUES (?, ?, ?, ?, ?)",
            (processo_id, doc_id, tipo, data_assinatura, nome),
        )
        conn.commit()


def listar_documentos(processo_id: int) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM documentos_pje WHERE processo_id = ?", (processo_id,)
        ).fetchall()
        return [dict(r) for r in rows]


# Log ------------------------------------------------------------------------

def registrar_log(processo_id: Optional[int], etapa: str, status: str, mensagem: str = ""):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO log_execucao (processo_id, etapa, status, mensagem) VALUES (?, ?, ?, ?)",
            (processo_id, etapa, status, mensagem),
        )
        conn.commit()


def listar_logs(processo_id: int) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM log_execucao WHERE processo_id = ? ORDER BY criado_em DESC",
            (processo_id,),
        ).fetchall()
        return [dict(r) for r in rows]


# Agente controle ------------------------------------------------------------

def _garantir_colunas_agente_controle(conn: sqlite3.Connection) -> None:
    existentes = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(agente_controle)").fetchall()
    }
    for coluna, definicao in COLUNAS_AGENTE_CONTROLE.items():
        if coluna not in existentes:
            conn.execute(f"ALTER TABLE agente_controle ADD COLUMN {coluna} {definicao}")


def _garantir_colunas_processos(conn: sqlite3.Connection) -> None:
    existentes = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(processos)").fetchall()
    }
    for coluna, definicao in COLUNAS_PROCESSOS.items():
        if coluna not in existentes:
            conn.execute(f"ALTER TABLE processos ADD COLUMN {coluna} {definicao}")


def _agora_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _snapshot_novo_ciclo() -> str:
    return json.dumps({"criado_em": _agora_iso()}, ensure_ascii=False)


def _obter_controle_agente_conn(conn: sqlite3.Connection) -> Optional[Dict[str, Any]]:
    _garantir_colunas_agente_controle(conn)
    row = conn.execute("SELECT * FROM agente_controle WHERE id = 1").fetchone()
    return dict(row) if row else None


def _inserir_controle_padrao(conn: sqlite3.Connection) -> Dict[str, Any]:
    conn.execute(
        """
        INSERT INTO agente_controle (
            id, comando, status, mensagem, pid, ciclo_snapshot
        ) VALUES (1, 'parar', 'parado', '', NULL, '{}')
        """
    )
    return _obter_controle_agente_conn(conn) or {}

def obter_controle_agente() -> Optional[Dict[str, Any]]:
    """Retorna o registro de controle do agente (id=1) ou None."""
    with get_conn() as conn:
        return _obter_controle_agente_conn(conn)


def criar_ou_atualizar_controle_agente(
    comando: Optional[str] = None,
    status: Optional[str] = None,
    mensagem: Optional[str] = None,
    pid: Optional[int] = None,
    ciclo_uuid: Optional[str] = None,
    ciclo_snapshot: Optional[str] = None,
    pausado_em: Optional[str] = None,
    retomado_em: Optional[str] = None,
) -> None:
    """
    Upsert na tabela agente_controle (id=1).
    Campos None são ignorados (mantêm valor atual).
    Usa BEGIN IMMEDIATE para evitar race condition entre API e agente.
    """
    with get_conn() as conn:
        try:
            conn.execute("BEGIN IMMEDIATE")
            _garantir_colunas_agente_controle(conn)
            row = conn.execute("SELECT id FROM agente_controle WHERE id = 1").fetchone()
            if row:
                campos = []
                vals = []
                for campo, valor in (
                    ("comando", comando),
                    ("status", status),
                    ("mensagem", mensagem),
                    ("pid", pid),
                    ("ciclo_uuid", ciclo_uuid),
                    ("ciclo_snapshot", ciclo_snapshot),
                    ("pausado_em", pausado_em),
                    ("retomado_em", retomado_em),
                ):
                    if valor is not None:
                        campos.append(f"{campo} = ?")
                        vals.append(valor)
                if campos:
                    campos.append("atualizado_em = CURRENT_TIMESTAMP")
                    conn.execute(
                        f"UPDATE agente_controle SET {', '.join(campos)} WHERE id = 1",
                        vals,
                    )
                    conn.commit()
            else:
                conn.execute(
                    """
                    INSERT INTO agente_controle (
                        id, comando, status, mensagem, pid, ciclo_uuid,
                        ciclo_snapshot, pausado_em, retomado_em
                    ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        comando or "parar",
                        status or "parado",
                        mensagem or "",
                        pid,
                        ciclo_uuid,
                        ciclo_snapshot or "{}",
                        pausado_em,
                        retomado_em,
                    ),
                )
                conn.commit()
        except Exception:
            conn.rollback()
            raise


def solicitar_inicio_agente() -> Dict[str, Any]:
    """Registra um pedido de início ou retomada de ciclo de forma atômica."""
    with get_conn() as conn:
        try:
            conn.execute("BEGIN IMMEDIATE")
            controle = _obter_controle_agente_conn(conn) or _inserir_controle_padrao(conn)
            status = controle.get("status", "parado")
            if status in ESTADOS_CICLO_ATIVO:
                conn.rollback()
                return {"accepted": False, "status": status, "ciclo_uuid": controle.get("ciclo_uuid")}

            retomando = bool(controle.get("ciclo_uuid")) and status in ESTADOS_CICLO_RETOMAVEL
            ciclo_uuid = controle.get("ciclo_uuid") if retomando else str(uuid.uuid4())
            ciclo_snapshot = (controle.get("ciclo_snapshot") or "{}") if retomando else _snapshot_novo_ciclo()
            proximo_status = "aguardando_login" if status == "aguardando_login" else "iniciando"

            ciclo_existente = conn.execute(
                "SELECT uuid FROM agente_ciclos WHERE uuid = ?",
                (ciclo_uuid,),
            ).fetchone()
            if ciclo_existente:
                conn.execute(
                    """
                    UPDATE agente_ciclos
                       SET status = ?,
                           atualizado_em = CURRENT_TIMESTAMP
                     WHERE uuid = ?
                    """,
                    (proximo_status, ciclo_uuid),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO agente_ciclos (uuid, rotulo, status)
                    VALUES (?, ?, ?)
                    """,
                    (ciclo_uuid, _rotulo_ciclo(), proximo_status),
                )

            conn.execute(
                """
                UPDATE agente_controle
                   SET comando = 'iniciar',
                       status = ?,
                       mensagem = ?,
                       ciclo_uuid = ?,
                       ciclo_snapshot = ?,
                       pausado_em = CASE WHEN ? THEN pausado_em ELSE NULL END,
                       retomado_em = CURRENT_TIMESTAMP,
                       atualizado_em = CURRENT_TIMESTAMP
                 WHERE id = 1
                """,
                (
                    proximo_status,
                    "Retomando ciclo pausado." if retomando else "Iniciando novo ciclo.",
                    ciclo_uuid,
                    ciclo_snapshot,
                    retomando,
                ),
            )
            conn.commit()
            return {
                "accepted": True,
                "resumed": retomando,
                "status": proximo_status,
                "ciclo_uuid": ciclo_uuid,
            }
        except Exception:
            conn.rollback()
            raise


def solicitar_parada_agente() -> Dict[str, Any]:
    """Solicita parada cooperativa preservando UUID e snapshot do ciclo."""
    with get_conn() as conn:
        try:
            conn.execute("BEGIN IMMEDIATE")
            controle = _obter_controle_agente_conn(conn) or _inserir_controle_padrao(conn)
            status = controle.get("status", "parado")
            if status in {"parado", "pausado", "interrompido", "erro_pausado"}:
                conn.execute(
                    """
                    UPDATE agente_controle
                       SET comando = 'parar',
                           atualizado_em = CURRENT_TIMESTAMP
                     WHERE id = 1
                    """
                )
                conn.commit()
                return {
                    "accepted": True,
                    "already_paused": True,
                    "status": status,
                    "ciclo_uuid": controle.get("ciclo_uuid"),
                }

            ciclo_uuid = controle.get("ciclo_uuid") or str(uuid.uuid4())
            ciclo_snapshot = controle.get("ciclo_snapshot") or _snapshot_novo_ciclo()
            conn.execute(
                """
                UPDATE agente_controle
                   SET comando = 'parar',
                       status = 'parando',
                       mensagem = 'Parada solicitada. Pausando no próximo ponto seguro.',
                       ciclo_uuid = ?,
                       ciclo_snapshot = ?,
                       pausado_em = COALESCE(pausado_em, CURRENT_TIMESTAMP),
                       atualizado_em = CURRENT_TIMESTAMP
                 WHERE id = 1
                """,
                (ciclo_uuid, ciclo_snapshot),
            )
            conn.commit()
            return {
                "accepted": True,
                "already_paused": False,
                "status": "parando",
                "ciclo_uuid": ciclo_uuid,
            }
        except Exception:
            conn.rollback()
            raise


def pausar_ciclo_agente(status: str, mensagem: str) -> None:
    """Marca o ciclo atual como pausado sem apagar UUID/snapshot."""
    criar_ou_atualizar_controle_agente(
        comando="parar",
        status=status,
        mensagem=mensagem,
        pausado_em=_agora_iso(),
    )


def listar_aprovados(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM processos WHERE status = 'aprovado' ORDER BY atualizado_em LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]


# Ciclos do agente -----------------------------------------------------------

def _rotulo_ciclo(agora: Optional[datetime] = None) -> str:
    base = agora or datetime.now()
    return base.strftime("Ciclo %d/%m/%Y %H:%M")


def _numero_sem_mascara(numero: str) -> str:
    return re.sub(r"\D", "", numero)


def _recalcular_contadores_ciclo(conn: sqlite3.Connection, ciclo_uuid: str) -> None:
    row = conn.execute(
        """
        SELECT
            COUNT(*) AS total_membros,
            SUM(CASE WHEN origem = 'novo_pje' THEN 1 ELSE 0 END) AS total_novos,
            SUM(CASE WHEN origem = 'rearmado' THEN 1 ELSE 0 END) AS total_rearmados
        FROM agente_ciclo_membros
        WHERE ciclo_uuid = ?
        """,
        (ciclo_uuid,),
    ).fetchone()
    status_rows = conn.execute(
        """
        SELECT p.status, COUNT(*) AS total
        FROM agente_ciclo_membros m
        JOIN processos p ON p.id = m.processo_id
        WHERE m.ciclo_uuid = ?
        GROUP BY p.status
        """,
        (ciclo_uuid,),
    ).fetchall()
    por_status = {r["status"]: r["total"] for r in status_rows}
    total_concluidos = sum(
        por_status.get(status, 0)
        for status in ("aguardando_aprovacao", "aprovado", "emitido")
    )
    total_erros = por_status.get("erro", 0)
    conn.execute(
        """
        UPDATE agente_ciclos
           SET total_membros = ?,
               total_novos = ?,
               total_rearmados = ?,
               total_concluidos = ?,
               total_erros = ?,
               atualizado_em = CURRENT_TIMESTAMP
         WHERE uuid = ?
        """,
        (
            row["total_membros"] or 0,
            row["total_novos"] or 0,
            row["total_rearmados"] or 0,
            total_concluidos,
            total_erros,
            ciclo_uuid,
        ),
    )


def criar_ciclo_agente() -> Dict[str, Any]:
    """Cria um ciclo persistido para o comando Iniciar Agente."""
    ciclo_uuid = str(uuid.uuid4())
    with get_conn() as conn:
        conn.execute("BEGIN IMMEDIATE")
        ativo = conn.execute(
            """
            SELECT *
            FROM agente_ciclos
            WHERE status IN ('iniciando', 'executando')
            ORDER BY criado_em DESC
            LIMIT 1
            """
        ).fetchone()
        if ativo:
            conn.rollback()
            return dict(ativo)
        conn.execute(
            """
            INSERT INTO agente_ciclos (uuid, rotulo, status)
            VALUES (?, ?, 'iniciando')
            """,
            (ciclo_uuid, _rotulo_ciclo()),
        )
        conn.commit()
    ciclo = obter_ciclo(ciclo_uuid)
    if ciclo is None:
        raise RuntimeError("Ciclo criado não encontrado")
    return ciclo


def obter_ciclo_atual() -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT *
            FROM agente_ciclos
            WHERE status IN ('iniciando', 'executando', 'aguardando_login')
            ORDER BY criado_em DESC
            LIMIT 1
            """
        ).fetchone()
        return dict(row) if row else None


def obter_ultimo_ciclo() -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM agente_ciclos ORDER BY criado_em DESC LIMIT 1"
        ).fetchone()
        return dict(row) if row else None


def obter_ciclo(ciclo_uuid: str) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM agente_ciclos WHERE uuid = ?", (ciclo_uuid,)
        ).fetchone()
        return dict(row) if row else None


def listar_membros_ciclo(ciclo_uuid: str) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT
                m.id,
                m.ciclo_uuid,
                m.processo_id,
                m.numero,
                m.numero_sem_mascara,
                m.origem,
                m.status_snapshot,
                m.criado_em,
                p.status AS status_atual
            FROM agente_ciclo_membros m
            JOIN processos p ON p.id = m.processo_id
            WHERE m.ciclo_uuid = ?
            ORDER BY m.id
            """,
            (ciclo_uuid,),
        ).fetchall()
        return [dict(r) for r in rows]


def obter_ciclo_com_membros(ciclo_uuid: str) -> Optional[Dict[str, Any]]:
    ciclo = obter_ciclo(ciclo_uuid)
    if not ciclo:
        return None
    ciclo["membros"] = listar_membros_ciclo(ciclo_uuid)
    return ciclo


def fechar_snapshot_ciclo(ciclo_uuid: str, numeros_pje: List[str]) -> Dict[str, Any]:
    """Fecha o lote do ciclo com novos do PJE e rearmados explicitamente."""
    vistos = set()
    numeros_normalizados = []
    for numero in numeros_pje:
        if numero in vistos:
            continue
        vistos.add(numero)
        numeros_normalizados.append(numero)

    with get_conn() as conn:
        conn.execute("BEGIN IMMEDIATE")
        ciclo = conn.execute(
            "SELECT * FROM agente_ciclos WHERE uuid = ?", (ciclo_uuid,)
        ).fetchone()
        if not ciclo:
            conn.rollback()
            raise ValueError(f"Ciclo não encontrado: {ciclo_uuid}")
        if ciclo["fechado_em"]:
            membros = conn.execute(
                """
                SELECT
                    m.id,
                    m.ciclo_uuid,
                    m.processo_id,
                    m.numero,
                    m.numero_sem_mascara,
                    m.origem,
                    m.status_snapshot,
                    m.criado_em,
                    p.status AS status_atual
                FROM agente_ciclo_membros m
                JOIN processos p ON p.id = m.processo_id
                WHERE m.ciclo_uuid = ?
                ORDER BY m.id
                """,
                (ciclo_uuid,),
            ).fetchall()
            ciclo_atual = dict(ciclo)
            ciclo_atual["membros"] = [dict(r) for r in membros]
            conn.rollback()
            return ciclo_atual

        _garantir_colunas_processos(conn)
        rearmados = conn.execute(
            """
            SELECT id, numero, numero_sem_mascara, status
            FROM processos
            WHERE reprocessar_solicitado_em IS NOT NULL
            ORDER BY reprocessar_solicitado_em, criado_em
            """
        ).fetchall()
        rearmados_consumidos = []
        for rearmado in rearmados:
            rearmados_consumidos.append(rearmado["id"])
            conn.execute(
                """
                INSERT OR IGNORE INTO agente_ciclo_membros (
                    ciclo_uuid,
                    processo_id,
                    numero,
                    numero_sem_mascara,
                    origem,
                    status_snapshot
                ) VALUES (?, ?, ?, ?, 'rearmado', ?)
                """,
                (
                    ciclo_uuid,
                    rearmado["id"],
                    rearmado["numero"],
                    rearmado["numero_sem_mascara"],
                    rearmado["status"],
                ),
            )

        if rearmados_consumidos:
            placeholders = ",".join("?" for _ in rearmados_consumidos)
            conn.execute(
                f"""
                UPDATE processos
                   SET reprocessar_solicitado_em = NULL,
                       reprocessar_solicitado_por = NULL,
                       reprocessar_motivo = NULL,
                       atualizado_em = CURRENT_TIMESTAMP
                 WHERE id IN ({placeholders})
                """,
                rearmados_consumidos,
            )

        for numero in numeros_normalizados:
            existente = conn.execute(
                "SELECT id, status, numero_sem_mascara FROM processos WHERE numero = ?",
                (numero,),
            ).fetchone()
            if existente is None:
                numero_sem_mascara = _numero_sem_mascara(numero)
                cur = conn.execute(
                    "INSERT INTO processos (numero, numero_sem_mascara) VALUES (?, ?)",
                    (numero, numero_sem_mascara),
                )
                processo_id = cur.lastrowid
                origem = "novo_pje"
                status_snapshot = "pendente"
            elif existente["status"] != "pendente":
                continue
            else:
                continue

            conn.execute(
                """
                INSERT OR IGNORE INTO agente_ciclo_membros (
                    ciclo_uuid,
                    processo_id,
                    numero,
                    numero_sem_mascara,
                    origem,
                    status_snapshot
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    ciclo_uuid,
                    processo_id,
                    numero,
                    numero_sem_mascara,
                    origem,
                    status_snapshot,
                ),
            )

        conn.execute(
            """
            UPDATE agente_ciclos
               SET status = 'executando',
                   fechado_em = COALESCE(fechado_em, CURRENT_TIMESTAMP),
                   atualizado_em = CURRENT_TIMESTAMP
             WHERE uuid = ?
            """,
            (ciclo_uuid,),
        )
        _recalcular_contadores_ciclo(conn, ciclo_uuid)
        conn.commit()

    ciclo = obter_ciclo_com_membros(ciclo_uuid)
    if ciclo is None:
        raise RuntimeError("Ciclo fechado não encontrado")
    return ciclo


def atualizar_contadores_ciclo(ciclo_uuid: str) -> None:
    with get_conn() as conn:
        conn.execute("BEGIN IMMEDIATE")
        _recalcular_contadores_ciclo(conn, ciclo_uuid)
        conn.commit()


def finalizar_ciclo(ciclo_uuid: str, status: str = "concluido", erro_msg: str = "") -> None:
    with get_conn() as conn:
        conn.execute("BEGIN IMMEDIATE")
        _recalcular_contadores_ciclo(conn, ciclo_uuid)
        conn.execute(
            """
            UPDATE agente_ciclos
               SET status = ?,
                   erro_msg = ?,
                   finalizado_em = CURRENT_TIMESTAMP,
                   atualizado_em = CURRENT_TIMESTAMP
             WHERE uuid = ?
            """,
            (status, erro_msg, ciclo_uuid),
        )
        conn.commit()


# Tarefas -------------------------------------------------------------------

def criar_tarefa(tipo: str, payload: Dict[str, Any], sistema_alvo: str, criado_por: str) -> int:
    """Insere nova tarefa e retorna o id."""
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO agente_tarefas (tipo, payload, sistema_alvo, criado_por) VALUES (?, ?, ?, ?)",
            (tipo, json.dumps(payload), sistema_alvo, criado_por),
        )
        conn.commit()
        return cur.lastrowid


def obter_tarefa(task_id: int) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM agente_tarefas WHERE id = ?", (task_id,)
        ).fetchone()
        if not row:
            return None
        tarefa = dict(row)
        for campo in ("payload", "resultado"):
            if tarefa.get(campo):
                try:
                    tarefa[campo] = json.loads(tarefa[campo])
                except json.JSONDecodeError:
                    pass
        return tarefa


def listar_tarefas(
    status: Optional[str] = None,
    tipo: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Tuple[int, List[Dict[str, Any]]]:
    with get_conn() as conn:
        where = ["1=1"]
        params: List[Any] = []
        if status:
            where.append("status = ?")
            params.append(status)
        if tipo:
            where.append("tipo = ?")
            params.append(tipo)

        where_sql = " AND ".join(where)

        total_row = conn.execute(
            f"SELECT COUNT(*) FROM agente_tarefas WHERE {where_sql}", params
        ).fetchone()
        total = total_row[0] if total_row else 0

        rows = conn.execute(
            f"SELECT * FROM agente_tarefas WHERE {where_sql} ORDER BY criado_em DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()

        items = []
        for row in rows:
            item = dict(row)
            for campo in ("payload", "resultado"):
                if item.get(campo):
                    try:
                        item[campo] = json.loads(item[campo])
                    except json.JSONDecodeError:
                        pass
            items.append(item)
        return total, items


def proxima_tarefa_pendente() -> Optional[Dict[str, Any]]:
    """
    Pega a próxima tarefa pendente (atomicamente) e marca como executando.
    Retorna None se não houver.
    """
    with get_conn() as conn:
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT * FROM agente_tarefas WHERE status = 'pendente' ORDER BY criado_em LIMIT 1"
            ).fetchone()
            if not row:
                conn.rollback()
                return None

            task_id = row["id"]
            conn.execute(
                "UPDATE agente_tarefas SET status = 'executando', iniciado_em = CURRENT_TIMESTAMP WHERE id = ?",
                (task_id,),
            )
            conn.commit()

            tarefa = dict(row)
            tarefa["status"] = "executando"
            if tarefa.get("payload"):
                try:
                    tarefa["payload"] = json.loads(tarefa["payload"])
                except json.JSONDecodeError:
                    pass
            return tarefa
        except Exception:
            conn.rollback()
            raise


def concluir_tarefa(
    task_id: int,
    status: str,
    resultado: Optional[Dict[str, Any]] = None,
    mensagem_erro: Optional[str] = None,
) -> bool:
    with get_conn() as conn:
        cur = conn.execute(
            """UPDATE agente_tarefas
               SET status = ?, resultado = ?, mensagem_erro = ?, concluido_em = CURRENT_TIMESTAMP
               WHERE id = ? AND status != 'cancelado'""",
            (status, json.dumps(resultado) if resultado else "{}", mensagem_erro or "", task_id),
        )
        conn.commit()
        return cur.rowcount > 0


def devolver_tarefa_pendente(task_id: int) -> bool:
    """Reverte uma tarefa em execução para pendente."""
    with get_conn() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT id FROM agente_tarefas WHERE id = ?", (task_id,)
        ).fetchone()
        if not row:
            conn.rollback()
            return False
        conn.execute(
            """UPDATE agente_tarefas
               SET status = 'pendente',
                   iniciado_em = NULL,
                   concluido_em = NULL,
                   mensagem_erro = NULL,
                   atualizado_em = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (task_id,),
        )
        conn.commit()
        return True


def cancelar_tarefa(task_id: int) -> bool:
    """Cancela uma tarefa pendente ou em execução. Retorna True se cancelou."""
    with get_conn() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT status FROM agente_tarefas WHERE id = ?", (task_id,)
        ).fetchone()
        if not row or row["status"] not in {"pendente", "executando"}:
            conn.rollback()
            return False
        conn.execute(
            """UPDATE agente_tarefas
               SET status = 'cancelado',
                   mensagem_erro = 'Cancelada pelo usuário',
                   concluido_em = CURRENT_TIMESTAMP,
                   atualizado_em = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (task_id,)
        )
        conn.commit()
        return True


def reenfileirar_tarefas_stale(max_age_minutes: int = 5) -> List[int]:
    """
    Reenfileira tarefas em execução há mais tempo que o limite.
    Retorna os IDs afetados.
    """
    with get_conn() as conn:
        conn.execute("BEGIN IMMEDIATE")
        rows = conn.execute(
            """
            SELECT id
            FROM agente_tarefas
            WHERE status = 'executando'
              AND iniciado_em IS NOT NULL
              AND iniciado_em <= datetime('now', ?)
            """,
            (f"-{max_age_minutes} minutes",),
        ).fetchall()
        ids = [row["id"] for row in rows]
        if not ids:
            conn.rollback()
            return []

        placeholders = ", ".join("?" for _ in ids)
        conn.execute(
            f"""
            UPDATE agente_tarefas
               SET status = 'pendente',
                   iniciado_em = NULL,
                   concluido_em = NULL,
                   atualizado_em = CURRENT_TIMESTAMP,
                   mensagem_erro = 'Tarefa re-enfileirada automaticamente após timeout de execução'
             WHERE id IN ({placeholders})
            """,
            ids,
        )
        conn.commit()
        return ids


def contar_tarefas_por_status() -> Dict[str, int]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT status, COUNT(*) as c FROM agente_tarefas GROUP BY status"
        ).fetchall()
        return {r["status"]: r["c"] for r in rows}
