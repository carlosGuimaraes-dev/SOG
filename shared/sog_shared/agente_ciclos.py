"""
Operações de domínio para controle do agente e ciclos.
"""
from datetime import datetime, timezone
import json
import re
import uuid
from typing import Any, Dict, List, Optional

from sog_shared import infra_db

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


def _numero_sem_mascara(numero: str) -> str:
    return re.sub(r"\D", "", numero)


def _recalcular_contadores_ciclo(conn, ciclo_uuid: str) -> None:
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


def listar_membros_ciclo(ciclo_uuid: str) -> List[Dict[str, Any]]:
    with infra_db.get_conn() as conn:
        infra_db._garantir_schema_runtime(conn)
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
    ciclo = obter_ciclo(ciclo_uuid)
    if not ciclo:
        return None
    ciclo["membros"] = listar_membros_ciclo(ciclo_uuid)
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
        ciclo = conn.execute(
            "SELECT * FROM agente_ciclos WHERE uuid = ?",
            (ciclo_uuid,),
        ).fetchone()
        if not ciclo:
            conn.rollback()
            raise ValueError(f"Ciclo não encontrado: {ciclo_uuid}")
        if ciclo["fechado_em"]:
            membros = listar_membros_ciclo(ciclo_uuid)
            ciclo_atual = dict(ciclo)
            ciclo_atual["membros"] = membros
            conn.rollback()
            return ciclo_atual

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
    with infra_db.get_conn() as conn:
        conn.execute("BEGIN IMMEDIATE")
        _recalcular_contadores_ciclo(conn, ciclo_uuid)
        conn.commit()


def finalizar_ciclo(ciclo_uuid: str, status: str = "concluido", erro_msg: str = "") -> None:
    with infra_db.get_conn() as conn:
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
