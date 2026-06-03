"""
Operações de domínio para tarefas assíncronas e suporte a sessões externas.
"""
import json
from typing import Any, Dict, List, Optional, Tuple

from sog_shared import infra_db


def criar_tarefa(tipo: str, payload: Dict[str, Any], sistema_alvo: str, criado_por: str) -> int:
    with infra_db.get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO agente_tarefas (tipo, payload, sistema_alvo, criado_por) VALUES (?, ?, ?, ?)",
            (tipo, json.dumps(payload), sistema_alvo, criado_por),
        )
        conn.commit()
        return cur.lastrowid


def obter_tarefa(task_id: int) -> Optional[Dict[str, Any]]:
    with infra_db.get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM agente_tarefas WHERE id = ?",
            (task_id,),
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
    with infra_db.get_conn() as conn:
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
            f"SELECT COUNT(*) FROM agente_tarefas WHERE {where_sql}",
            params,
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
    with infra_db.get_conn() as conn:
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
    with infra_db.get_conn() as conn:
        cur = conn.execute(
            """UPDATE agente_tarefas
               SET status = ?, resultado = ?, mensagem_erro = ?, concluido_em = CURRENT_TIMESTAMP
               WHERE id = ? AND status != 'cancelado'""",
            (status, json.dumps(resultado) if resultado else "{}", mensagem_erro or "", task_id),
        )
        conn.commit()
        return cur.rowcount > 0


def devolver_tarefa_pendente(task_id: int) -> bool:
    with infra_db.get_conn() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT id FROM agente_tarefas WHERE id = ?",
            (task_id,),
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
    with infra_db.get_conn() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT status FROM agente_tarefas WHERE id = ?",
            (task_id,),
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
            (task_id,),
        )
        conn.commit()
        return True


def reenfileirar_tarefas_stale(max_age_minutes: int = 5) -> List[int]:
    with infra_db.get_conn() as conn:
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
    with infra_db.get_conn() as conn:
        rows = conn.execute(
            "SELECT status, COUNT(*) as c FROM agente_tarefas GROUP BY status"
        ).fetchall()
        return {r["status"]: r["c"] for r in rows}
