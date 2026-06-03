"""
Operações de domínio para processos e aprovação.
"""
import json
from typing import Any, Dict, List, Optional

from sog_shared import infra_db

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

_CAMPOS_JSON_DADOS_PROCESSO = (
    "sucumbentes",
    "outros_itens",
    "compensacao",
    "custas_pagas",
)


def processo_existe(numero: str) -> Optional[Dict[str, Any]]:
    with infra_db.get_conn() as conn:
        row = conn.execute(
            "SELECT id, status, tentativas FROM processos WHERE numero = ?",
            (numero,),
        ).fetchone()
        if row is None:
            return None
        return {"id": row["id"], "status": row["status"], "tentativas": row["tentativas"]}


def inserir_processo(numero: str, numero_sem_mascara: str) -> int:
    with infra_db.get_conn() as conn:
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
) -> None:
    with infra_db.get_conn() as conn:
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
    with infra_db.get_conn() as conn:
        try:
            conn.execute("BEGIN IMMEDIATE")
            infra_db._garantir_schema_runtime(conn)
            row = conn.execute(
                "SELECT * FROM processos WHERE id = ?",
                (processo_id,),
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
                "SELECT * FROM processos WHERE id = ?",
                (processo_id,),
            ).fetchone()
            conn.commit()
            return {"accepted": True, "processo": dict(atualizado)}
        except Exception:
            conn.rollback()
            raise


def listar_aguardando_aprovacao(
    limit: int = 1000,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    with infra_db.get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM processos WHERE status = 'aguardando_aprovacao' ORDER BY atualizado_em DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]


def listar_aprovados(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    with infra_db.get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM processos WHERE status = 'aprovado' ORDER BY atualizado_em LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]


def listar_processos_para_fila(
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, List[Dict[str, Any]]]:
    with infra_db.get_conn() as conn:
        aguardando = conn.execute(
            "SELECT * FROM processos WHERE status = 'aguardando_aprovacao' ORDER BY atualizado_em DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        manuais = conn.execute(
            "SELECT * FROM processos WHERE status = 'pendente_manual' ORDER BY atualizado_em DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return {
            "aguardando_aprovacao": [dict(r) for r in aguardando],
            "pendente_manual": [dict(r) for r in manuais],
        }


def listar_historico_processos(
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[Dict[str, Any]]:
    sql = """SELECT p.numero, d.polo_ativo, d.valor_total_recolher,
                    p.status, p.atualizado_em, d.obs_operador
             FROM processos p
             LEFT JOIN dados_processo d ON d.processo_id = p.id
             WHERE p.status IN ('emitido', 'rejeitado')
             ORDER BY p.atualizado_em DESC"""
    params: tuple[Any, ...] = ()
    if limit is not None and offset is not None:
        sql += " LIMIT ? OFFSET ?"
        params = (limit, offset)

    with infra_db.get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]


def obter_processo(processo_id: int) -> Optional[Dict[str, Any]]:
    with infra_db.get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM processos WHERE id = ?",
            (processo_id,),
        ).fetchone()
        return dict(row) if row else None


def obter_numero_processo(processo_id: int) -> Optional[str]:
    processo = obter_processo(processo_id)
    if not processo:
        return None
    return processo["numero"]


def salvar_dados_processo(processo_id: int, dados: Dict[str, Any]) -> int:
    campos = list(dados.keys())
    invalidas = set(campos) - COLUNAS_PERMITIDAS_DADOS_PROCESSO
    if invalidas:
        raise ValueError(
            f"Colunas não permitidas em dados_processo: {sorted(invalidas)}"
        )

    valores = list(dados.values())
    for i, valor in enumerate(valores):
        if isinstance(valor, (list, dict)):
            valores[i] = json.dumps(valor, ensure_ascii=False)

    with infra_db.get_conn() as conn:
        existente = conn.execute(
            "SELECT id FROM dados_processo WHERE processo_id = ? ORDER BY id DESC LIMIT 1",
            (processo_id,),
        ).fetchone()
        if existente:
            if campos:
                set_sql = ", ".join(f"{campo} = ?" for campo in campos)
                conn.execute(
                    f"UPDATE dados_processo SET {set_sql} WHERE id = ?",
                    (*valores, existente["id"]),
                )
            conn.commit()
            return existente["id"]

        placeholders = ", ".join(["?"] * len(campos))
        colunas = ", ".join(campos)
        if campos:
            cur = conn.execute(
                f"INSERT INTO dados_processo (processo_id, {colunas}) VALUES (?, {placeholders})",
                (processo_id, *valores),
            )
        else:
            cur = conn.execute(
                "INSERT INTO dados_processo (processo_id) VALUES (?)",
                (processo_id,),
            )
        conn.commit()
        return cur.lastrowid


def obter_dados_processo(processo_id: int) -> Optional[Dict[str, Any]]:
    with infra_db.get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM dados_processo WHERE processo_id = ? ORDER BY id DESC LIMIT 1",
            (processo_id,),
        ).fetchone()
        if not row:
            return None
        dados = dict(row)
        for campo in _CAMPOS_JSON_DADOS_PROCESSO:
            if dados.get(campo):
                try:
                    dados[campo] = json.loads(dados[campo])
                except json.JSONDecodeError:
                    pass
        return dados


def salvar_documento(
    processo_id: int,
    doc_id: str,
    tipo: str,
    data_assinatura: str,
    nome: str,
) -> int:
    with infra_db.get_conn() as conn:
        existente = conn.execute(
            "SELECT id FROM documentos_pje WHERE processo_id = ? AND doc_id = ?",
            (processo_id, doc_id),
        ).fetchone()
        if existente:
            conn.execute(
                """
                UPDATE documentos_pje
                   SET tipo = ?, data_assinatura = ?, nome = ?
                 WHERE id = ?
                """,
                (tipo, data_assinatura, nome, existente["id"]),
            )
            conn.commit()
            return existente["id"]
        cur = conn.execute(
            """
            INSERT INTO documentos_pje (processo_id, doc_id, tipo, data_assinatura, nome)
            VALUES (?, ?, ?, ?, ?)
            """,
            (processo_id, doc_id, tipo, data_assinatura, nome),
        )
        conn.commit()
        return cur.lastrowid


def registrar_log(
    processo_id: Optional[int],
    etapa: str,
    status: str,
    mensagem: str = "",
    chave_idempotencia: Optional[str] = None,
) -> int:
    with infra_db.get_conn() as conn:
        infra_db._garantir_schema_runtime(conn)
        existente = None
        if chave_idempotencia is not None:
            existente = conn.execute(
                """
                SELECT id
                FROM log_execucao
                WHERE processo_id IS ?
                  AND etapa = ?
                  AND status = ?
                  AND chave_idempotencia = ?
                LIMIT 1
                """,
                (processo_id, etapa, status, chave_idempotencia),
            ).fetchone()
        if existente is None:
            existente = conn.execute(
                """
                SELECT id
                FROM log_execucao
                WHERE processo_id IS ?
                  AND etapa = ?
                  AND status = ?
                  AND COALESCE(mensagem, '') = COALESCE(?, '')
                LIMIT 1
                """,
                (processo_id, etapa, status, mensagem),
            ).fetchone()
        if existente:
            return existente["id"]
        cur = conn.execute(
            """
            INSERT INTO log_execucao (
                processo_id,
                etapa,
                status,
                mensagem,
                chave_idempotencia
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (processo_id, etapa, status, mensagem, chave_idempotencia),
        )
        conn.commit()
        return cur.lastrowid


def salvar_evidencia_emissao(
    processo_id: int,
    etapa: str,
    referencia_arquivo: Optional[str] = None,
    referencia_externa: Optional[str] = None,
    metadados: Optional[Dict[str, Any]] = None,
) -> int:
    metadados_json = json.dumps(metadados or {}, ensure_ascii=False)
    with infra_db.get_conn() as conn:
        existente = conn.execute(
            """
            SELECT id
            FROM evidencias_emissao
            WHERE processo_id = ? AND etapa = ?
            LIMIT 1
            """,
            (processo_id, etapa),
        ).fetchone()
        if existente:
            conn.execute(
                """
                UPDATE evidencias_emissao
                   SET referencia_arquivo = ?,
                       referencia_externa = ?,
                       metadados = ?,
                       atualizado_em = CURRENT_TIMESTAMP
                 WHERE id = ?
                """,
                (referencia_arquivo, referencia_externa, metadados_json, existente["id"]),
            )
            conn.commit()
            return existente["id"]

        cur = conn.execute(
            """
            INSERT INTO evidencias_emissao (
                processo_id,
                etapa,
                referencia_arquivo,
                referencia_externa,
                metadados
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (processo_id, etapa, referencia_arquivo, referencia_externa, metadados_json),
        )
        conn.commit()
        return cur.lastrowid


def obter_evidencia_emissao(processo_id: int, etapa: str) -> Optional[Dict[str, Any]]:
    with infra_db.get_conn() as conn:
        row = conn.execute(
            """
            SELECT *
            FROM evidencias_emissao
            WHERE processo_id = ? AND etapa = ?
            LIMIT 1
            """,
            (processo_id, etapa),
        ).fetchone()
        if not row:
            return None
        evidencia = dict(row)
        if evidencia.get("metadados"):
            try:
                evidencia["metadados"] = json.loads(evidencia["metadados"])
            except json.JSONDecodeError:
                pass
        return evidencia


def obter_detalhe_processo(processo_id: int) -> Optional[Dict[str, Any]]:
    with infra_db.get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM processos WHERE id = ?",
            (processo_id,),
        ).fetchone()
        if not row:
            return None

        processo = dict(row)
        dados = obter_dados_processo(processo_id)
        log_rows = conn.execute(
            "SELECT * FROM log_execucao WHERE processo_id = ? ORDER BY criado_em DESC",
            (processo_id,),
        ).fetchall()
        doc_rows = conn.execute(
            "SELECT * FROM documentos_pje WHERE processo_id = ?",
            (processo_id,),
        ).fetchall()

        return {
            "processo": processo,
            "dados": dados,
            "logs": [dict(r) for r in log_rows],
            "documentos": [dict(r) for r in doc_rows],
        }


def aprovar_processo(processo_id: int, usuario: str) -> bool:
    with infra_db.get_conn() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT status FROM processos WHERE id = ?",
            (processo_id,),
        ).fetchone()
        if not row:
            conn.rollback()
            return False
        if row["status"] != "aguardando_aprovacao":
            conn.rollback()
            raise ValueError("status_not_allowed")
        conn.execute(
            "UPDATE processos SET status = 'aprovado', atualizado_em = CURRENT_TIMESTAMP WHERE id = ?",
            (processo_id,),
        )
        conn.execute(
            "INSERT INTO log_execucao (processo_id, etapa, status, mensagem) VALUES (?, ?, ?, ?)",
            (processo_id, "aprovacao", "ok", f"Aprovado por {usuario}"),
        )
        conn.commit()
        return True


def rejeitar_processo(processo_id: int, usuario: str, observacao: str) -> bool:
    observacao_segura = observacao.replace("\n", " ").replace("\r", "")[:500]
    with infra_db.get_conn() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT status FROM processos WHERE id = ?",
            (processo_id,),
        ).fetchone()
        if not row:
            conn.rollback()
            return False
        if row["status"] != "aguardando_aprovacao":
            conn.rollback()
            raise ValueError("status_not_allowed")
        conn.execute(
            "UPDATE processos SET status = 'rejeitado', atualizado_em = CURRENT_TIMESTAMP WHERE id = ?",
            (processo_id,),
        )
        conn.execute(
            "INSERT INTO log_execucao (processo_id, etapa, status, mensagem) VALUES (?, ?, ?, ?)",
            (processo_id, "rejeicao", "ok", f"Rejeitado por {usuario}: {observacao_segura}"),
        )
        conn.execute(
            "UPDATE dados_processo SET obs_operador = ? WHERE processo_id = ?",
            (observacao, processo_id),
        )
        conn.commit()
        return True
