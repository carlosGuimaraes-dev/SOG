"""
Snapshot e membros dos ciclos do agente.
"""
import re
from typing import Any, Dict, List, Optional

from sog_shared import infra_db
from sog_shared.agente_ciclo_contadores import recalcular_contadores_ciclo


def _numero_sem_mascara(numero: str) -> str:
    return re.sub(r"\D", "", numero)


def _obter_ciclo_conn(conn, ciclo_uuid: str) -> Optional[Dict[str, Any]]:
    row = conn.execute(
        "SELECT * FROM agente_ciclos WHERE uuid = ?",
        (ciclo_uuid,),
    ).fetchone()
    return dict(row) if row else None


def _listar_membros_ciclo_conn(conn, ciclo_uuid: str) -> List[Dict[str, Any]]:
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
            m.processado_em,
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


def listar_membros_ciclo(ciclo_uuid: str) -> List[Dict[str, Any]]:
    with infra_db.get_conn() as conn:
        infra_db._garantir_schema_runtime(conn)
        return _listar_membros_ciclo_conn(conn, ciclo_uuid)


def marcar_membro_ciclo_processado(ciclo_uuid: str, processo_id: int) -> bool:
    with infra_db.get_conn() as conn:
        infra_db._garantir_schema_runtime(conn)
        cur = conn.execute(
            """
            UPDATE agente_ciclo_membros
               SET processado_em = COALESCE(processado_em, CURRENT_TIMESTAMP)
             WHERE ciclo_uuid = ? AND processo_id = ?
            """,
            (ciclo_uuid, processo_id),
        )
        conn.commit()
        return cur.rowcount > 0


def obter_ciclo_com_membros(ciclo_uuid: str) -> Optional[Dict[str, Any]]:
    with infra_db.get_conn() as conn:
        ciclo = _obter_ciclo_conn(conn, ciclo_uuid)
        if not ciclo:
            return None
        ciclo["membros"] = _listar_membros_ciclo_conn(conn, ciclo_uuid)
        return ciclo


def fechar_snapshot_ciclo(ciclo_uuid: str, numeros_pje: List[str]) -> Dict[str, Any]:
    vistos = set()
    numeros_normalizados = []
    for numero in numeros_pje:
        if numero in vistos:
            continue
        vistos.add(numero)
        numeros_normalizados.append(numero)

    with infra_db.get_conn() as conn:
        conn.execute("BEGIN IMMEDIATE")
        infra_db._garantir_schema_runtime(conn)
        ciclo = _obter_ciclo_conn(conn, ciclo_uuid)
        if not ciclo:
            conn.rollback()
            raise ValueError(f"Ciclo não encontrado: {ciclo_uuid}")
        if ciclo["fechado_em"]:
            ciclo["membros"] = _listar_membros_ciclo_conn(conn, ciclo_uuid)
            conn.rollback()
            return ciclo

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
        recalcular_contadores_ciclo(conn, ciclo_uuid)
        conn.commit()

    ciclo = obter_ciclo_com_membros(ciclo_uuid)
    if ciclo is None:
        raise RuntimeError("Ciclo fechado não encontrado")
    return ciclo
