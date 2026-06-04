"""
Operações de domínio para controle do agente e ciclos.
"""
from datetime import datetime, timezone
import json
import uuid
from typing import Any, Dict, Optional

from sog_shared import agente_ciclo_contadores, agente_ciclo_snapshot, infra_db

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


def _agora_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _snapshot_novo_ciclo() -> str:
    return json.dumps({"criado_em": _agora_iso()}, ensure_ascii=False)


def _obter_controle_agente_conn(conn) -> Optional[Dict[str, Any]]:
    infra_db._garantir_schema_runtime(conn)
    row = conn.execute("SELECT * FROM agente_controle WHERE id = 1").fetchone()
    return dict(row) if row else None


def _inserir_controle_padrao(conn) -> Dict[str, Any]:
    conn.execute(
        """
        INSERT INTO agente_controle (
            id, comando, status, mensagem, pid, ciclo_snapshot
        ) VALUES (1, 'parar', 'parado', '', NULL, '{}')
        """
    )
    return _obter_controle_agente_conn(conn) or {}


def obter_controle_agente() -> Optional[Dict[str, Any]]:
    with infra_db.get_conn() as conn:
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
    with infra_db.get_conn() as conn:
        try:
            conn.execute("BEGIN IMMEDIATE")
            infra_db._garantir_schema_runtime(conn)
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
    with infra_db.get_conn() as conn:
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
    with infra_db.get_conn() as conn:
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
    criar_ou_atualizar_controle_agente(
        comando="parar",
        status=status,
        mensagem=mensagem,
        pausado_em=_agora_iso(),
    )


def _rotulo_ciclo(agora: Optional[datetime] = None) -> str:
    base = agora or datetime.now()
    return base.strftime("Ciclo %d/%m/%Y %H:%M")


def criar_ciclo_agente() -> Dict[str, Any]:
    """Cria um ciclo persistido para fluxos que exigem bootstrap explícito."""
    ciclo_uuid = str(uuid.uuid4())
    with infra_db.get_conn() as conn:
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
    with infra_db.get_conn() as conn:
        controle = _obter_controle_agente_conn(conn)
        if controle and controle.get("ciclo_uuid"):
            ciclo = conn.execute(
                "SELECT * FROM agente_ciclos WHERE uuid = ?",
                (controle["ciclo_uuid"],),
            ).fetchone()
            if ciclo:
                return dict(ciclo)

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
    with infra_db.get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM agente_ciclos ORDER BY criado_em DESC LIMIT 1"
        ).fetchone()
        return dict(row) if row else None


def obter_ciclo(ciclo_uuid: str) -> Optional[Dict[str, Any]]:
    with infra_db.get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM agente_ciclos WHERE uuid = ?",
            (ciclo_uuid,),
        ).fetchone()
        return dict(row) if row else None


def _obter_ciclo_mais_recente_do_processo_conn(conn, processo_id: int) -> Optional[str]:
    row = conn.execute(
        """
        SELECT m.ciclo_uuid
        FROM agente_ciclo_membros m
        JOIN agente_ciclos c ON c.uuid = m.ciclo_uuid
        WHERE m.processo_id = ?
        ORDER BY c.criado_em DESC, m.id DESC
        LIMIT 1
        """,
        (processo_id,),
    ).fetchone()
    if not row:
        return None
    return row["ciclo_uuid"]


def listar_membros_ciclo(ciclo_uuid: str):
    return agente_ciclo_snapshot.listar_membros_ciclo(ciclo_uuid)


def marcar_membro_ciclo_processado(ciclo_uuid: str, processo_id: int) -> bool:
    return agente_ciclo_snapshot.marcar_membro_ciclo_processado(ciclo_uuid, processo_id)


def obter_ciclo_com_membros(ciclo_uuid: str):
    return agente_ciclo_snapshot.obter_ciclo_com_membros(ciclo_uuid)


def fechar_snapshot_ciclo(ciclo_uuid: str, numeros_pje):
    return agente_ciclo_snapshot.fechar_snapshot_ciclo(ciclo_uuid, numeros_pje)


def _recalcular_contadores_ciclo(conn, ciclo_uuid: str) -> None:
    agente_ciclo_contadores.recalcular_contadores_ciclo(conn, ciclo_uuid)


def atualizar_contadores_ciclo(ciclo_uuid: str) -> None:
    agente_ciclo_contadores.atualizar_contadores_ciclo(ciclo_uuid)


def atualizar_contadores_ciclo_do_processo(processo_id: int) -> None:
    agente_ciclo_contadores.atualizar_contadores_ciclo_do_processo(processo_id)


def finalizar_ciclo(ciclo_uuid: str, status: str = "concluido", erro_msg: str = "") -> None:
    agente_ciclo_contadores.finalizar_ciclo(ciclo_uuid, status=status, erro_msg=erro_msg)
