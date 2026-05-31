# Plano Técnico — Integração Completa PJe/SISTJWEB (Backend ↔ Agente)

> **Escopo:** Permitir que o backend exponha ao frontend ações sob demanda nos sistemas PJe e SISTJWEB, além de orquestrar o pipeline automático existente.
>
> **Data:** 2026-05-18
> **Versão:** 1.0

---

## 1. Visão Geral da Solução

A comunicação atual (SQLite polling com 1 linha de comando `iniciar`/`parar`) evolui para um **modelo de fila de tarefas via SQLite**.

Cada ação sob demanda (consultar etiqueta, baixar PDF, preencher SISTJWEB, etc.) vira uma linha na tabela `agente_tarefas` com:
- `tipo` (enum de comandos)
- `payload` (parâmetros em JSON)
- `status` (`pendente` → `executando` → `concluido`/`erro`)
- `resultado` (retorno em JSON)

O backend insere a tarefa e retorna `task_id` imediatamente (padrão async job). O frontend acompanha via polling em `GET /tarefas/{task_id}`. O agente consome tarefas pendentes entre as iterações do pipeline automático, preservando 100% da compatibilidade com o loop existente.

**Decisão arquitetural central:** manter SQLite como canal de comunicação. Não introduzir Redis, RabbitMQ, WebSocket nem servidor HTTP no agente. A fila SQLite é o menor salto evolutivo possível a partir da arquitetura atual.

---

## 2. Arquitetura de Comunicação

### 2.1 Modelo de Fila SQLite

```
┌──────────┐   POST /tarefas        ┌─────────┐   INSERT         ┌──────────┐
│ Frontend │ ─────────────────────> │ FastAPI │ ───────────────> │ SQLite   │
│          │   {tipo, payload}      │  API    │   agente_tarefas │          │
└──────────┘                        └─────────┘                  └──────────┘
      ^                                                    │
      │                                                    │ polling (cada ~30s)
      │                                                    v
GET /tarefas/{id}                                    ┌──────────┐
(polling a cada 2s)                                  │ Agente   │
                                                     │ Serviço  │
                                                     └──────────┘
```

**Fluxo de vida de uma tarefa:**

1. **Criação:** Backend recebe request, valida input, insere `agente_tarefas(status='pendente')`, retorna `{task_id}`.
2. **Consumo:** Agente, no loop principal, entre iterações do pipeline, faz `SELECT * FROM agente_tarefas WHERE status='pendente' ORDER BY criado_em LIMIT 1` com `BEGIN IMMEDIATE`.
3. **Execução:** Agente atualiza status para `executando`, executa a ação pontual via PjeClient/SistjClient, grava `resultado` JSON e status `concluido` (ou `erro`).
4. **Consulta:** Frontend faz polling em `GET /tarefas/{task_id}` até status != `pendente`/`executando`.

### 2.2 Por que não WebSocket / HTTP no agente / Message Broker

| Opção | Prós | Contras |
|-------|------|---------|
| WebSocket API→Agente | Real-time | Requer servidor WS no agente; complica firewall; Playwright não é async-friendly |
| HTTP polling agente→API | Padrão REST | Inverte dependência (agente precisa conhecer URL da API); retry/circuit breaker necessários |
| RabbitMQ / Redis | Escalável | Nova infraestrutura; Docker Compose mais complexo; overkill para <10 req/min |
| **SQLite fila (escolhida)** | Zero nova infra; ambos já compartilham banco; BEGIN IMMEDIATE garante atomicidade; histórico persistente | Latência até 30s (mitigável); não escala para 100+ req/s (não é nosso caso) |

### 2.3 Prioridade entre Pipeline e Tarefas

O agente processa **até 3 tarefas pendentes por iteração do loop** antes de executar o pipeline. Isso garante:
- Ações sob demanda não ficam bloqueadas por um pipeline longo.
- Pipeline automático continua rodando quando a fila esvazia.
- Não há starvation do pipeline (limite de 3 tarefas/iteração).

**Algoritmo no loop:**
```python
def _loop_iteration(self):
    self._atualizar_heartbeat()
    
    # 1. Verifica comando iniciar/parar (compat existente)
    # ... lógica atual ...
    
    # 2. Processa tarefas pendentes (nova)
    tarefas_processadas = self._processar_tarefas_pendentes(max_tarefas=3)
    if tarefas_processadas > 0 and self._ha_mais_tarefas_pendentes():
        return  # volta ao loop sem dormir, processa mais tarefas
    
    # 3. Pipeline automático (lógica atual)
    # ... executa / dorme ...
```

### 2.4 Lock por Sistema (proteção contra execução paralela)

O agente mantém locks em memória (suficiente pois é processo único):

```python
self._locks = {"pje": False, "sistj": False}
```

Cada tarefa define `sistema_alvo` (`pje`, `sistj`, `ambos`). Antes de executar:
1. Verifica se o(s) sistema(s) estão locked.
2. Se sim, pula esta tarefa e tenta a próxima (de sistema diferente).
3. Se não, adquire lock, executa, libera lock.

O pipeline automático também adquire locks antes de usar cada sistema. Isso evita que uma tarefa "consultar documentos" concorra com o pipeline no mesmo browser.

**Decisão de baixa reversibilidade:** a tabela `agente_tarefas` e o mecanismo de lock em memória são aditivos, mas se descartados futuramente, requerem migração de dados ou truncamento da tabela. Reversibilidade é **média**.

---

## 3. Novos Endpoints da API

### 3.1 Rotas de Tarefas (novo arquivo: `api/src/rotas/tarefas.py`)

| Método | Path | Descrição | Request Body | Response |
|--------|------|-----------|-------------|----------|
| `POST` | `/tarefas` | Cria nova tarefa | `CriarTarefaRequest` | `TarefaResponse` |
| `GET` | `/tarefas` | Lista tarefas (paginado) | Query: `status`, `tipo`, `limit`, `offset` | `TarefaListResponse` |
| `GET` | `/tarefas/{task_id}` | Detalhe de uma tarefa | — | `TarefaResponse` |
| `POST` | `/tarefas/{task_id}/cancelar` | Cancela tarefa pendente | — | `TarefaResponse` |

### 3.2 Rotas de PJe (novo arquivo: `api/src/rotas/pje.py`)

| Método | Path | Descrição | Request Body | Response |
|--------|------|-----------|-------------|----------|
| `POST` | `/pje/consultar-etiqueta` | Lista processos da etiqueta configurada | — | `TarefaResponse` |
| `POST` | `/pje/processos/{numero}/documentos` | Lista documentos de um processo | — | `TarefaResponse` |
| `POST` | `/pje/documentos/{doc_id}/pdf` | Baixa PDF de um documento | `BaixarPdfRequest` | `TarefaResponse` |
| `GET` | `/pje/sessao` | Verifica status da sessão PJe | — | `SessaoStatusResponse` |
| `POST` | `/pje/reautenticar` | Força reautenticação interativa no PJe | — | `TarefaResponse` |

### 3.3 Rotas de SISTJWEB (novo arquivo: `api/src/rotas/sistjweb.py`)

| Método | Path | Descrição | Request Body | Response |
|--------|------|-----------|-------------|----------|
| `POST` | `/sistj/preencher/{processo_id}` | Preenche planilha SISTJWEB | — | `TarefaResponse` |
| `POST` | `/sistj/gravar-aprovar/{processo_id}` | Grava e aprova no SISTJWEB | — | `TarefaResponse` |
| `GET` | `/sistj/sessao` | Verifica status da sessão SISTJWEB | — | `SessaoStatusResponse` |
| `POST` | `/sistj/reautenticar` | Força reautenticação interativa no SISTJWEB | — | `TarefaResponse` |

### 3.4 Rotas de Ações de Processo (novo arquivo: `api/src/rotas/acoes.py`)

| Método | Path | Descrição | Request Body | Response |
|--------|------|-----------|-------------|----------|
| `POST` | `/processos/{id}/reprocessar` | Reprocessa pipeline para processo específico | — | `TarefaResponse` |
| `POST` | `/processos/{id}/anexar-demonstrativo` | Anexa demonstrativo PDF no PJe | — | `TarefaResponse` |

### 3.5 Rotas de Dashboard (novo arquivo: `api/src/rotas/dashboard.py`)

| Método | Path | Descrição | Response |
|--------|------|-----------|----------|
| `GET` | `/dashboard/sessoes` | Estado das sessões PJe + SISTJWEB + fila de tarefas | `DashboardSessoesResponse` |

---

## 4. Novos Schemas Pydantic

Adicionar a `shared/sog_shared/schemas.py` e `api/src/schemas.py` (duplicação mantida por compatibilidade atual; idealmente unificar no shared no futuro).

### 4.1 Tarefas

```python
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class CriarTarefaRequest(BaseModel):
    tipo: str = Field(..., description="Tipo da tarefa (ex: consultar_etiqueta_pje)")
    payload: Dict[str, Any] = Field(default_factory=dict)


class TarefaResponse(BaseModel):
    id: int
    tipo: str
    status: str  # pendente | executando | concluido | erro | cancelado
    payload: Dict[str, Any]
    resultado: Optional[Dict[str, Any]] = None
    mensagem_erro: Optional[str] = None
    sistema_alvo: Optional[str] = None
    criado_em: Optional[str] = None
    iniciado_em: Optional[str] = None
    concluido_em: Optional[str] = None


class TarefaListResponse(BaseModel):
    total: int
    items: list[TarefaResponse]
```

### 4.2 Sessão

```python
class SessaoStatusResponse(BaseModel):
    sistema: str  # pje | sistj
    logado: bool
    mensagem: str
    ultima_verificacao: Optional[str] = None
```

### 4.3 Dashboard

```python
class DashboardSessoesResponse(BaseModel):
    pje: SessaoStatusResponse
    sistj: SessaoStatusResponse
    agente_online: bool
    agente_status: str
    tarefas_pendentes: int
    tarefas_executando: int
```

### 4.4 Payloads específicos

```python
class BaixarPdfRequest(BaseModel):
    numero_processo: str = Field(..., pattern=r"^\d{7}-?\d{2}\.?\d{4}\.?\d\.?\d{2}\.?\d{4}$")
    # doc_id vem do path
```

---

## 5. Alterações no Banco de Dados

### 5.1 Nova tabela: `agente_tarefas`

Adicionar ao `shared/sog_shared/schema.sql`:

```sql
CREATE TABLE IF NOT EXISTS agente_tarefas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL,
    payload TEXT DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'pendente',
    -- status: pendente | executando | concluido | erro | cancelado
    resultado TEXT DEFAULT '{}',
    mensagem_erro TEXT,
    sistema_alvo TEXT,
    -- sistema_alvo: pje | sistj | ambos
    criado_por TEXT,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    iniciado_em DATETIME,
    concluido_em DATETIME,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tarefas_status ON agente_tarefas(status, criado_em);
CREATE INDEX IF NOT EXISTS idx_tarefas_sistema ON agente_tarefas(sistema_alvo, status);
```

### 5.2 Funções de banco a adicionar em `shared/sog_shared/db.py`

```python
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
) -> None:
    with get_conn() as conn:
        conn.execute(
            """UPDATE agente_tarefas
               SET status = ?, resultado = ?, mensagem_erro = ?, concluido_em = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (status, json.dumps(resultado) if resultado else '{}', mensagem_erro or '', task_id),
        )
        conn.commit()


def cancelar_tarefa(task_id: int) -> bool:
    """Cancela uma tarefa se ainda estiver pendente. Retorna True se cancelou."""
    with get_conn() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT status FROM agente_tarefas WHERE id = ?", (task_id,)
        ).fetchone()
        if not row or row["status"] != "pendente":
            conn.rollback()
            return False
        conn.execute(
            "UPDATE agente_tarefas SET status = 'cancelado', atualizado_em = CURRENT_TIMESTAMP WHERE id = ?",
            (task_id,),
        )
        conn.commit()
        return True


def contar_tarefas_por_status() -> Dict[str, int]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT status, COUNT(*) as c FROM agente_tarefas GROUP BY status"
        ).fetchall()
        return {r["status"]: r["c"] for r in rows}
```

---

## 6. Alterações no Agente

### 6.1 Novo módulo: `agente/src/modulos/executor_tarefas.py`

Este módulo isola a lógica de execução de tarefas do loop do serviço.

```python
"""
Executor de tarefas sob demanda do agente.
Mapeia tipos de tarefa para funções que usam PjeClient/SistjClient.
"""
import json
import tempfile
from typing import Dict, Any, Callable

from sog_shared import db
from modulos.pje import PjeClient
from modulos.sistjweb import SistjClient
from modulos.auth_manager import ReautenticacaoNecessariaError
from utils.logger import info, erro, aviso

# Registry de handlers
_HANDLERS: Dict[str, Callable] = {}


def registrar(tipo: str):
    """Decorador para registrar handler de tarefa."""
    def wrapper(fn: Callable):
        _HANDLERS[tipo] = fn
        return fn
    return wrapper


def executar_tarefa(tarefa: Dict[str, Any], pje: PjeClient, sistj: SistjClient) -> Dict[str, Any]:
    """Executa uma tarefa e retorna o resultado."""
    tipo = tarefa["tipo"]
    payload = tarefa.get("payload") or {}
    
    handler = _HANDLERS.get(tipo)
    if not handler:
        raise ValueError(f"Tipo de tarefa desconhecido: {tipo}")
    
    return handler(payload, pje, sistj)


def tipos_suportados() -> list[str]:
    return list(_HANDLERS.keys())


# ── Handlers ──────────────────────────────────────────────────────────

@registrar("consultar_etiqueta_pje")
def _consultar_etiqueta(payload, pje, sistj):
    pje.garantir_autenticado()
    numeros = pje.coletar_lista_processos()
    return {"processos": numeros, "total": len(numeros)}


@registrar("consultar_documentos_pje")
def _consultar_documentos(payload, pje, sistj):
    numero = payload["numero_processo"]
    pje.garantir_autenticado()
    docs, textos = pje.coletar_documentos(numero)
    # Não persistimos no banco automaticamente (apenas retornamos)
    return {
        "documentos": docs,
        "numero_processo": numero,
    }


@registrar("baixar_pdf_pje")
def _baixar_pdf(payload, pje, sistj):
    numero = payload["numero_processo"]
    doc_id = payload["doc_id"]
    pje.garantir_autenticado()
    
    # Precisamos estar na página do processo
    # O PjeClient.baixar_documento_pdf assume que a página atual é a do processo
    # Portanto precisamos navegar até o processo primeiro
    # Nota: isso pode exigir ajuste em pje.py para expor navegação ao processo
    
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        caminho = tmp.name
    
    # Navega até o processo (reutilizando lógica existente)
    from modulos.pje import escape_for_css, _safe_click
    pje.page.goto(pje.page.url.split("#")[0], wait_until="networkidle")
    pje.page.wait_for_timeout(2000)
    
    numero_escapado = escape_for_css(numero)
    seletores = [
        f"a:has-text('{numero_escapado}')",
        f"td:has-text('{numero_escapado}')",
        f"span:has-text('{numero_escapado}')",
    ]
    if not _safe_click(pje.page, seletores, timeout=15000):
        raise RuntimeError(f"Não foi possível navegar até o processo {numero}")
    pje.page.wait_for_load_state("networkidle")
    pje.page.wait_for_timeout(3000)
    
    sucesso = pje.baixar_documento_pdf(doc_id, caminho)
    return {"sucesso": sucesso, "caminho": caminho if sucesso else None}


@registrar("verificar_sessao_pje")
def _verificar_sessao_pje(payload, pje, sistj):
    # Não dispara autenticação — apenas verifica estado atual
    try:
        logado = pje._esta_logado(pje.page)
        return {"logado": logado, "url_atual": pje.page.url}
    except Exception:
        return {"logado": False, "url_atual": None}


@registrar("verificar_sessao_sistj")
def _verificar_sessao_sistj(payload, pje, sistj):
    try:
        logado = sistj._esta_logado(sistj.page)
        return {"logado": logado, "url_atual": sistj.page.url}
    except Exception:
        return {"logado": False, "url_atual": None}


@registrar("preencher_sistj")
def _preencher_sistj(payload, pje, sistj):
    processo_id = payload["processo_id"]
    dados = db.obter_dados_processo(processo_id)
    if not dados:
        raise ValueError(f"Dados do processo {processo_id} não encontrados")
    
    numero = dados.get("numero", "")
    numero_sem_mascara = dados.get("numero_sem_mascara", "")
    
    # Reconstrói payload do pipeline
    from pipeline import _construir_payload
    from modulos.datajud import consultar as datajud_consultar
    from regras import detectar_area, obter_regras_outros_itens
    
    area = dados.get("area_direito", "")
    if not area:
        area = detectar_area(dados.get("classe", ""), dados.get("feito", ""))
    
    payload_sistj = {
        "numero_sem_mascara": numero_sem_mascara,
        "numero": numero,
        "instancia": dados.get("instancia", "1ª Instância"),
        "processo_eletronico": dados.get("processo_eletronico", 1),
        "circunscricao": dados.get("circunscricao", ""),
        "competencia": dados.get("competencia", ""),
        "feito": dados.get("feito", ""),
        "classe": dados.get("classe", ""),
        "valor_causa": dados.get("valor_causa", ""),
        "data_distribuicao": dados.get("data_distribuicao", ""),
        "polo_ativo": dados.get("polo_ativo", ""),
        "polo_passivo": dados.get("polo_passivo", "Não Há"),
        "tipo_guia": dados.get("tipo_guia", ""),
        "pro_rata": dados.get("pro_rata", 0),
        "sucumbentes": dados.get("sucumbentes", []),
        "custas_pagas": dados.get("custas_pagas", []),
        **{k: v for k, v in dados.items() if k.startswith("ids_")},
        "area_direito": area,
    }
    
    sistj.garantir_autenticado()
    resultado = sistj.preencher(payload_sistj, numero)
    
    db.salvar_dados_processo(processo_id, {**payload_sistj, **resultado})
    db.atualizar_status(processo_id, "aguardando_aprovacao")
    db.registrar_log(processo_id, "sistjweb", "ok", f"Tarefa manual: {resultado.get('screenshot_path', '')}")
    
    return {"screenshot_path": resultado.get("screenshot_path"), "valor_total_recolher": resultado.get("valor_total_recolher")}


@registrar("gravar_aprovar_sistj")
def _gravar_aprovar_sistj(payload, pje, sistj):
    processo_id = payload["processo_id"]
    dados = db.obter_dados_processo(processo_id)
    if not dados:
        raise ValueError(f"Dados do processo {processo_id} não encontrados")
    
    numero_sem_mascara = dados.get("numero_sem_mascara", "")
    sistj.garantir_autenticado()
    caminho_pdf = sistj.gravar_e_aprovar(numero_sem_mascara)
    
    return {"caminho_pdf": caminho_pdf}


@registrar("anexar_demonstrativo_pje")
def _anexar_demonstrativo_pje(payload, pje, sistj):
    processo_id = payload["processo_id"]
    dados = db.obter_dados_processo(processo_id)
    if not dados:
        raise ValueError(f"Dados do processo {processo_id} não encontrados")
    
    numero = dados.get("numero", "")
    numero_sem_mascara = dados.get("numero_sem_mascara", "")
    
    # Procura PDF do demonstrativo nos diretórios conhecidos
    from pathlib import Path
    from config import DEMONSTRATIVOS_DIR
    
    caminho_pdf = Path(DEMONSTRATIVOS_DIR) / f"{numero_sem_mascara}.pdf"
    if not caminho_pdf.exists():
        # Tenta com número formatado
        caminho_pdf = Path(DEMONSTRATIVOS_DIR) / f"{numero}.pdf"
    if not caminho_pdf.exists():
        raise FileNotFoundError(f"PDF do demonstrativo não encontrado para {numero}")
    
    pje.garantir_autenticado()
    sucesso = pje.anexar_demonstrativo(numero, str(caminho_pdf))
    
    if sucesso:
        db.atualizar_status(processo_id, "emitido")
        db.registrar_log(processo_id, "emissao", "ok", f"Anexado via tarefa: {caminho_pdf}")
    
    return {"sucesso": sucesso, "caminho_pdf": str(caminho_pdf)}


@registrar("reprocessar_processo")
def _reprocessar_processo(payload, pje, sistj):
    processo_id = payload["processo_id"]
    from banco import db as db_agente
    
    with db_agente.get_conn() as conn:
        row = conn.execute("SELECT numero, numero_sem_mascara FROM processos WHERE id = ?", (processo_id,)).fetchone()
        if not row:
            raise ValueError(f"Processo {processo_id} não encontrado")
        numero = row["numero"]
        numero_sem_mascara = row["numero_sem_mascara"]
    
    # Reseta status para permitir reprocessamento
    db.atualizar_status(processo_id, "pendente", erro_msg="", incrementar_tentativa=False)
    
    # Chama pipeline para um único processo
    from pipeline import processar_processo
    processar_processo(numero, numero_sem_mascara, pje, sistj)
    
    return {"numero_processo": numero, "status": "reprocessado"}


@registrar("reautenticar_pje")
def _reautenticar_pje(payload, pje, sistj):
    pje.garantir_autenticado()
    return {"logado": True}


@registrar("reautenticar_sistj")
def _reautenticar_sistj(payload, pje, sistj):
    sistj.garantir_autenticado()
    return {"logado": True}
```

### 6.2 Alterações em `agente/src/servico.py`

Adicionar:

```python
from modulos.executor_tarefas import executar_tarefa, tipos_suportados
from sog_shared.db import (
    # ... imports existentes ...
    proxima_tarefa_pendente,
    concluir_tarefa,
)

# Na classe AgenteServico.__init__:
def __init__(self):
    # ... existente ...
    self._locks = {"pje": False, "sistj": False}
    self._tarefas_por_iteracao = 3

# Novo método:
def _processar_tarefas_pendentes(self, max_tarefas: int = 3) -> int:
    """Processa até N tarefas pendentes. Retorna quantas processou."""
    processadas = 0
    for _ in range(max_tarefas):
        tarefa = proxima_tarefa_pendente()
        if not tarefa:
            break
        
        sistema = tarefa.get("sistema_alvo", "ambos")
        sistemas = [sistema] if sistema != "ambos" else ["pje", "sistj"]
        
        # Verifica lock
        if any(self._locks[s] for s in sistemas):
            # Devolve à fila como pendente
            concluir_tarefa(tarefa["id"], "pendente")
            aviso(f"Tarefa {tarefa['id']} adiada — sistema {sistema} ocupado.")
            continue
        
        # Adquire lock
        for s in sistemas:
            self._locks[s] = True
        
        try:
            info(f"Executando tarefa {tarefa['id']}: {tarefa['tipo']}")
            resultado = executar_tarefa(tarefa, self.pje, self.sistj)
            concluir_tarefa(tarefa["id"], "concluido", resultado=resultado)
            info(f"Tarefa {tarefa['id']} concluída.")
        except ReautenticacaoNecessariaError as e:
            concluir_tarefa(tarefa["id"], "erro", mensagem_erro=f"Reautenticação necessária: {e.sistema}")
            self._set_status("aguardando_login", f"Sessão {e.sistema} expirada durante tarefa.")
        except Exception as e:
            erro(f"Erro na tarefa {tarefa['id']}: {e}")
            concluir_tarefa(tarefa["id"], "erro", mensagem_erro=str(e))
        finally:
            for s in sistemas:
                self._locks[s] = False
        
        processadas += 1
    
    return processadas

# Novo método auxiliar:
def _ha_mais_tarefas_pendentes(self) -> bool:
    from sog_shared.db import get_conn
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM agente_tarefas WHERE status = 'pendente'"
        ).fetchone()
        return (row[0] if row else 0) > 0
```

E modificar `_loop_iteration` para chamar `_processar_tarefas_pendentes` antes do pipeline (ver seção 2.3).

### 6.3 Alterações em `agente/src/pipeline.py`

O pipeline automático (`rodar_pipeline`, `emitir_pendentes`) também deve respeitar os locks. No entanto, como o pipeline roda no thread principal e já adquire o browser exclusivamente, ele não compete consigo mesmo. O lock é relevante apenas se decidirmos rodar tarefas em thread separado (não é o caso no MVP).

**Ação:** nenhuma alteração necessária no pipeline para o MVP. O loop principal garante que tarefas e pipeline não executam simultaneamente.

---

## 7. Rotas da API (implementação detalhada)

### 7.1 `api/src/rotas/tarefas.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from auth import get_current_user
from limiter import limiter
from sog_shared import db
from schemas import TarefaResponse, TarefaListResponse, CriarTarefaRequest

router = APIRouter(prefix="/tarefas", tags=["tarefas"])

SISTEMA_POR_TIPO = {
    "consultar_etiqueta_pje": "pje",
    "consultar_documentos_pje": "pje",
    "baixar_pdf_pje": "pje",
    "verificar_sessao_pje": "pje",
    "reautenticar_pje": "pje",
    "preencher_sistj": "sistj",
    "gravar_aprovar_sistj": "sistj",
    "verificar_sessao_sistj": "sistj",
    "reautenticar_sistj": "sistj",
    "anexar_demonstrativo_pje": "ambos",
    "reprocessar_processo": "ambos",
}

TIPOS_VALIDOS = set(SISTEMA_POR_TIPO.keys())


@router.post("", response_model=TarefaResponse)
@limiter.limit("20/minute")
def criar_tarefa(
    request: Request,
    req: CriarTarefaRequest,
    user: str = Depends(get_current_user),
):
    if req.tipo not in TIPOS_VALIDOS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo inválido. Válidos: {', '.join(TIPOS_VALIDOS)}",
        )
    
    task_id = db.criar_tarefa(
        tipo=req.tipo,
        payload=req.payload,
        sistema_alvo=SISTEMA_POR_TIPO[req.tipo],
        criado_por=user,
    )
    tarefa = db.obter_tarefa(task_id)
    return tarefa


@router.get("", response_model=TarefaListResponse)
@limiter.limit("30/minute")
def listar_tarefas(
    request: Request,
    status: str = Query(None),
    tipo: str = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: str = Depends(get_current_user),
):
    total, items = db.listar_tarefas(status=status, tipo=tipo, limit=limit, offset=offset)
    return {"total": total, "items": items}


@router.get("/{task_id}", response_model=TarefaResponse)
@limiter.limit("60/minute")
def obter_tarefa(
    task_id: int,
    request: Request,
    user: str = Depends(get_current_user),
):
    tarefa = db.obter_tarefa(task_id)
    if not tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return tarefa


@router.post("/{task_id}/cancelar", response_model=TarefaResponse)
@limiter.limit("10/minute")
def cancelar_tarefa(
    task_id: int,
    request: Request,
    user: str = Depends(get_current_user),
):
    tarefa = db.obter_tarefa(task_id)
    if not tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    if tarefa.get("criado_por") != user:
        raise HTTPException(status_code=403, detail="Não autorizado a cancelar esta tarefa")
    
    cancelado = db.cancelar_tarefa(task_id)
    if not cancelado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tarefa não pode ser cancelada (já em execução ou concluída)",
        )
    
    return db.obter_tarefa(task_id)
```

### 7.2 `api/src/rotas/pje.py`

```python
import re
from fastapi import APIRouter, Depends, HTTPException, status, Request
from auth import get_current_user
from limiter import limiter
from sog_shared import db
from schemas import TarefaResponse, SessaoStatusResponse, BaixarPdfRequest

router = APIRouter(prefix="/pje", tags=["pje"])

_RE_CNJ = re.compile(r"^\d{7}-?\d{2}\.?\d{4}\.?\d\.?\d{2}\.?\d{4}$")


def _criar_tarefa_helper(tipo: str, payload: dict, user: str) -> TarefaResponse:
    sistema = {"consultar_etiqueta_pje": "pje", "consultar_documentos_pje": "pje",
               "baixar_pdf_pje": "pje", "reautenticar_pje": "pje"}[tipo]
    task_id = db.criar_tarefa(tipo=tipo, payload=payload, sistema_alvo=sistema, criado_por=user)
    return db.obter_tarefa(task_id)


@router.post("/consultar-etiqueta", response_model=TarefaResponse)
@limiter.limit("5/minute")
def consultar_etiqueta(request: Request, user: str = Depends(get_current_user)):
    return _criar_tarefa_helper("consultar_etiqueta_pje", {}, user)


@router.post("/processos/{numero}/documentos", response_model=TarefaResponse)
@limiter.limit("10/minute")
def consultar_documentos(numero: str, request: Request, user: str = Depends(get_current_user)):
    if not _RE_CNJ.match(numero):
        raise HTTPException(status_code=400, detail="Número de processo inválido (CNJ)")
    return _criar_tarefa_helper("consultar_documentos_pje", {"numero_processo": numero}, user)


@router.post("/documentos/{doc_id}/pdf", response_model=TarefaResponse)
@limiter.limit("10/minute")
def baixar_pdf(
    doc_id: str,
    req: BaixarPdfRequest,
    request: Request,
    user: str = Depends(get_current_user),
):
    if not doc_id or not doc_id.isdigit():
        raise HTTPException(status_code=400, detail="doc_id inválido")
    return _criar_tarefa_helper("baixar_pdf_pje", {
        "numero_processo": req.numero_processo,
        "doc_id": doc_id,
    }, user)


@router.get("/sessao", response_model=SessaoStatusResponse)
@limiter.limit("10/minute")
def sessao_pje(request: Request, user: str = Depends(get_current_user)):
    # Cria tarefa para verificar sessão
    task_id = db.criar_tarefa(
        tipo="verificar_sessao_pje",
        payload={},
        sistema_alvo="pje",
        criado_por=user,
    )
    # Para verificação de sessão, fazemos polling síncrono com timeout curto
    import time
    for _ in range(20):  # 20 x 500ms = 10s
        time.sleep(0.5)
        tarefa = db.obter_tarefa(task_id)
        if tarefa["status"] in ("concluido", "erro"):
            resultado = tarefa.get("resultado") or {}
            return {
                "sistema": "pje",
                "logado": resultado.get("logado", False),
                "mensagem": "Sessão ativa" if resultado.get("logado") else "Sessão inativa",
                "ultima_verificacao": tarefa["concluido_em"],
            }
    return {
        "sistema": "pje",
        "logado": False,
        "mensagem": "Timeout verificando sessão",
        "ultima_verificacao": None,
    }


@router.post("/reautenticar", response_model=TarefaResponse)
@limiter.limit("2/minute")
def reautenticar_pje(request: Request, user: str = Depends(get_current_user)):
    return _criar_tarefa_helper("reautenticar_pje", {}, user)
```

### 7.3 `api/src/rotas/sistjweb.py`

Estrutura análoga à do PJe. Endpoints criam tarefas do tipo correspondente.

```python
# POST /sistj/preencher/{processo_id}
# POST /sistj/gravar-aprovar/{processo_id}
# GET /sistj/sessao
# POST /sistj/reautenticar
```

### 7.4 `api/src/rotas/acoes.py`

```python
# POST /processos/{id}/reprocessar
# POST /processos/{id}/anexar-demonstrativo
```

### 7.5 `api/src/rotas/dashboard.py`

```python
from fastapi import APIRouter, Depends, Request
from auth import get_current_user
from limiter import limiter
from sog_shared import db
from schemas import DashboardSessoesResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/sessoes", response_model=DashboardSessoesResponse)
@limiter.limit("30/minute")
def dashboard_sessoes(request: Request, user: str = Depends(get_current_user)):
    controle = db.obter_controle_agente() or {}
    from datetime import datetime, timezone
    online = False
    if controle.get("atualizado_em"):
        try:
            atualizado = controle["atualizado_em"]
            if isinstance(atualizado, str):
                if atualizado.endswith('Z'):
                    atualizado = atualizado[:-1] + '+00:00'
                ultimo = datetime.fromisoformat(atualizado)
            else:
                ultimo = atualizado
            if ultimo.tzinfo is None:
                ultimo = ultimo.replace(tzinfo=timezone.utc)
            diff = (datetime.now(timezone.utc) - ultimo).total_seconds()
            online = diff < 90
        except Exception:
            pass
    
    status_counts = db.contar_tarefas_por_status()
    
    return {
        "pje": {
            "sistema": "pje",
            "logado": False,  # será preenchido via tarefa em W4
            "mensagem": "Desconhecido",
            "ultima_verificacao": None,
        },
        "sistj": {
            "sistema": "sistj",
            "logado": False,
            "mensagem": "Desconhecido",
            "ultima_verificacao": None,
        },
        "agente_online": online,
        "agente_status": controle.get("status", "desconhecido"),
        "tarefas_pendentes": status_counts.get("pendente", 0),
        "tarefas_executando": status_counts.get("executando", 0),
    }
```

**Nota:** No W4, o dashboard de sessões pode usar tarefas de verificação periódicas ou um cache no banco.

---

## 8. Segurança

### 8.1 Rate Limiting

- `POST /pje/*` e `POST /sistj/*`: **5-10/minuto** (ações que tocam sistemas externos)
- `POST /tarefas`: **20/minuto** (criação genérica)
- `GET /tarefas/{id}`: **60/minuto** (polling do frontend)
- `POST /pje/reautenticar`, `POST /sistj/reautenticar`: **2/minuto** (evita spam de navegador visível)
- `POST /processos/{id}/reprocessar`: **5/minuto**

### 8.2 Validação de Inputs

- Número de processo: regex CNJ (`\d{7}-?\d{2}\.?\d{4}\.?\d\.?\d{2}\.?\d{4}`)
- `doc_id`: apenas dígitos (`^\d+$`)
- `processo_id`: inteiro positivo, verificado se existe no banco
- `tipo` de tarefa: whitelist explícita (`TIPOS_VALIDOS`)
- `payload`: schema Pydantic por tipo (validação estruturada)

### 8.3 Proteção contra Execução Paralela no Mesmo Sistema

1. **Lock em memória no agente** (`self._locks`), suficiente pois o agente é processo único.
2. Se uma tarefa requer sistema que está locked, ela é **devolvida à fila** (`status='pendente'`) e processada na próxima iteração.
3. Pipeline automático e tarefas nunca executam simultaneamente no mesmo browser pois compartilham o loop principal.
4. Se no futuro o agente for distribuído (múltiplos processos), o lock deve migrar para o banco (coluna `locked_by` na `agente_controle` ou uso de `BEGIN IMMEDIATE` com update condicional).

### 8.4 Isolamento de Erros

- Exceção em uma tarefa não quebra o loop do agente.
- Tarefas com erro são marcadas como `erro` com mensagem, mas o agente continua processando as próximas.
- Timeout de tarefa: se uma tarefa travar, o agente pode ser reiniciado. A tarefa ficará como `executando` — adicionar mecanismo de "stale task detection" no backend (tarefa `executando` há >5 minutos é considerada stale e pode ser reprocessada).

### 8.5 Autorização

- Cancelamento de tarefa: apenas o usuário que criou pode cancelar.
- Futuro: campo `role` no token JWT para distinguir admin/operador.

---

## 9. Critérios de Aceite por Wave

### Wave 1 — Infraestrutura da Fila de Tarefas

- [ ] Tabela `agente_tarefas` criada no schema SQLite
- [ ] Funções `criar_tarefa`, `obter_tarefa`, `listar_tarefas`, `proxima_tarefa_pendente`, `concluir_tarefa`, `cancelar_tarefa` implementadas em `sog_shared/db.py`
- [ ] Schemas `TarefaResponse`, `TarefaListResponse`, `CriarTarefaRequest` adicionados
- [ ] Endpoints `POST /tarefas`, `GET /tarefas`, `GET /tarefas/{id}`, `POST /tarefas/{id}/cancelar` funcionais
- [ ] Módulo `agente/src/modulos/executor_tarefas.py` criado com registry de handlers vazio (só scaffolding)
- [ ] Agente consome tarefas pendentes no loop (máximo 3/iteração) e marca como `executando`/`concluido`/`erro`
- [ ] Teste: criar tarefa via API → verificar que agente a processa (handler dummy) → resultado retornado
- [ ] Pipeline automático continua funcionando (teste de regressão)

### Wave 2 — Consultas em Tempo Real (Read-Only)

- [ ] Handler `consultar_etiqueta_pje` funcional — retorna lista de números CNJ
- [ ] Handler `consultar_documentos_pje` funcional — retorna documentos de um processo
- [ ] Handler `baixar_pdf_pje` funcional — baixa PDF e retorna caminho
- [ ] Handler `verificar_sessao_pje` funcional — retorna booleano de login
- [ ] Handler `verificar_sessao_sistj` funcional — retorna booleano de login
- [ ] Endpoints `POST /pje/consultar-etiqueta`, `/pje/processos/{n}/documentos`, `/pje/documentos/{id}/pdf`, `/pje/sessao`
- [ ] Endpoints `GET /sistj/sessao`
- [ ] Rate limiting aplicado em todos os novos endpoints
- [ ] Frontend pode fazer polling em `/tarefas/{id}` e receber resultado em <60s

### Wave 3 — Ações Sob Demanda (Write)

- [ ] Handler `preencher_sistj` funcional — preenche planilha para processo existente
- [ ] Handler `gravar_aprovar_sistj` funcional — grava e aprova no SISTJWEB
- [ ] Handler `anexar_demonstrativo_pje` funcional — anexa PDF no PJe
- [ ] Handler `reprocessar_processo` funcional — reexecuta pipeline para processo específico
- [ ] Endpoints `POST /sistj/preencher/{id}`, `/sistj/gravar-aprovar/{id}`
- [ ] Endpoints `POST /processos/{id}/reprocessar`, `/processos/{id}/anexar-demonstrativo`
- [ ] Validação de `processo_id` (existe no banco, status adequado)
- [ ] Locks por sistema funcionam: tarefa de PJe não executa enquanto pipeline usa PJe
- [ ] Teste de integração: aprovar processo no dashboard → criar tarefa de gravar/aprovar → agente executa → status muda para emitido

### Wave 4 — Dashboard Avançado e Refinamentos

- [ ] Endpoint `GET /dashboard/sessoes` retorna estado consolidado
- [ ] Tarefas de reautenticação (`POST /pje/reautenticar`, `/sistj/reautenticar`) disparam navegador visível no agente
- [ ] Dashboard mostra sessões PJe/SISTJWEB em tempo real (via tarefas de verificação periódicas ou cache)
- [ ] Detecção de tarefas stale (executando >5 min) — backend pode re-enfileirar
- [ ] Cancelamento de tarefa funciona e libera lock no agente
- [ ] Documentação dos endpoints (OpenAPI já gerado pelo FastAPI)
- [ ] Teste de carga: 5 tarefas simultâneas enfileiradas → processadas sequencialmente sem deadlock

---

## 10. Ordem de Implementação Sugerida (Waves Incrementais)

```
Wave 1 — Infra da Fila
├── shared/sog_shared/schema.sql          (+ tabela agente_tarefas)
├── shared/sog_shared/db.py               (+ funções da fila)
├── shared/sog_shared/schemas.py          (+ schemas de tarefa)
├── api/src/schemas.py                    (+ schemas de tarefa)
├── api/src/rotas/tarefas.py              (novo — CRUD tarefas)
├── api/src/app.py                        (+ include_router tarefas)
├── agente/src/modulos/executor_tarefas.py (novo — registry vazio)
└── agente/src/servico.py                 (+ _processar_tarefas_pendentes)

Wave 2 — Consultas Read-Only
├── agente/src/modulos/executor_tarefas.py (+ handlers PJe read-only)
├── api/src/rotas/pje.py                  (novo)
├── api/src/rotas/sistjweb.py             (sessão apenas)
├── api/src/app.py                        (+ include_router pje, sistjweb)
└── Testes manuais de consulta

Wave 3 — Ações Write
├── agente/src/modulos/executor_tarefas.py (+ handlers write)
├── api/src/rotas/sistjweb.py             (+ preencher, gravar-aprovar)
├── api/src/rotas/acoes.py                (novo — reprocessar, anexar)
├── api/src/app.py                        (+ include_router acoes)
└── Testes de integração end-to-end

Wave 4 — Dashboard e Polish
├── api/src/rotas/dashboard.py            (novo)
├── api/src/app.py                        (+ include_router dashboard)
├── api/src/rotas/pje.py                  (+ reautenticar)
├── api/src/rotas/sistjweb.py             (+ reautenticar)
├── Stale task detection                  (api/src/rotas/tarefas.py)
└── Testes de concorrência e regressão
```

---

## 11. Riscos e Pontos de Atenção

| Risco | Prob. | Impacto | Mitigação |
|-------|-------|---------|-----------|
| Tarefa travada em `executando` (agente crasha) | Média | Médio | Stale detection no backend; timeout de 5min; operador pode cancelar/recriar |
| Playwright não responde durante tarefa (site lento) | Alta | Baixo | Retry automático já existente nos métodos PjeClient/SistjClient; tarefa marca `erro` após retries |
| Pipeline automático fica starvation se fila grande | Baixa | Baixo | Limite de 3 tarefas/iteração; se necessário, aumentar prioridade do pipeline em horário configurável |
| SQLite WAL mode cresce indefinidamente (tarefas antigas) | Baixa | Baixo | Adicionar job de limpeza (W4): deletar tarefas `concluido`/`erro`/`cancelado` com >30 dias |
| Frontend faz polling excessivo | Baixa | Baixo | Rate limit 60/min em GET /tarefas/{id}; recomendar intervalo de 2s no frontend |
| Reautenticação interativa bloqueia tarefas subsequentes | Média | Médio | Tarefa de reautenticar usa sistema `pje`/`sistj` — lock impede outras; UX do frontend deve indicar "Aguardando login manual" |
| Agente tenta baixar PDF mas navegador não está na página do processo | Média | Médio | Handler `baixar_pdf_pje` deve navegar até o processo antes de chamar `baixar_documento_pdf`; testar com mock |

---

## 12. Decisões de Baixa Reversibilidade

1. **Tabela `agente_tarefas` no schema SQLite**
   - Uma vez criada e populada, removê-la requer migração ou truncamento.
   - Mitigação: a tabela é aditiva; não modifica tabelas existentes.
   - Reversibilidade: **média**.

2. **Lock em memória no agente (`self._locks`)**
   - Se no futuro o agente for distribuído (múltiplos processos), o lock em memória não funciona.
   - Mitigação: a mudança para lock no banco é localizada (apenas `servico.py` e funções de consumo).
   - Reversibilidade: **alta** (refatoração localizada).

3. **Handlers de tarefa que usam `garantir_autenticado()` (navegador visível como fallback)**
   - Se uma tarefa de consulta disparar navegador visível, pode ser inesperado para o operador.
   - Mitigação: handlers de "verificar sessão" NÃO disparam fallback; apenas leem estado atual. Tarefas de ação documentam no resultado que reautenticação foi necessária.
   - Reversibilidade: **alta** (comportamental, não estrutural).

---

## 13. Notas para o Executor

### 13.1 Compatibilidade com `agente_controle` existente

A tabela `agente_controle` continua existindo e funcional. O comando `iniciar`/`parar` não muda. O agente lê `agente_controle` **e** `agente_tarefas` a cada iteração. Se o comando for `parar`, o agente para mesmo que haja tarefas pendentes (elas ficam na fila para quando reiniciar).

### 13.2 Compartilhamento de schemas

Atualmente há duplicação entre `shared/sog_shared/schemas.py` e `api/src/schemas.py`. Para este plano, adicione os novos schemas em **ambos** os arquivos. Uma tarefa futura (não escopo deste plano) deve unificar em um único arquivo compartilhado.

### 13.3 Imports no agente

O agente usa `sys.path.insert` para acessar `shared/`. Certifique-se de que `executor_tarefas.py` importe `sog_shared.db` corretamente (via `sys.path` já configurado em `servico.py`).

### 13.4 Testes recomendados

- **Teste de regressão:** iniciar agente, enviar `iniciar`, aguardar pipeline rodar → deve continuar funcionando.
- **Teste de tarefa:** `curl -X POST /api/v1/tarefas -d '{"tipo":"verificar_sessao_pje","payload":{}}'` → aguardar 30s → `GET /tarefas/{id}` deve retornar `status=concluido`.
- **Teste de lock:** enfileirar tarefa `consultar_etiqueta_pje` e `preencher_sistj` simultaneamente → agente deve processar uma por vez, respeitando sistema_alvo.
