"""
Contadores agregados dos ciclos do agente.
"""
from sog_shared import infra_db

_STATUS_CONCLUIDOS = ("aguardando_aprovacao", "aprovado", "emitido")


def recalcular_contadores_ciclo(conn, ciclo_uuid: str) -> None:
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
    total_concluidos = sum(por_status.get(status, 0) for status in _STATUS_CONCLUIDOS)
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


def atualizar_contadores_ciclo(ciclo_uuid: str) -> None:
    with infra_db.get_conn() as conn:
        conn.execute("BEGIN IMMEDIATE")
        recalcular_contadores_ciclo(conn, ciclo_uuid)
        conn.commit()


def finalizar_ciclo(ciclo_uuid: str, status: str = "concluido", erro_msg: str = "") -> None:
    with infra_db.get_conn() as conn:
        conn.execute("BEGIN IMMEDIATE")
        recalcular_contadores_ciclo(conn, ciclo_uuid)
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
