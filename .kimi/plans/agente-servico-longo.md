# Plano Técnico — Agente como Serviço Longo (Daemon)

> **Escopo:** Transformar o agente de script de execução única em serviço longo/daemon com loop infinito, comunicação bidirecional com o dashboard via SQLite, autenticação por storage state com fallback interativo, e emissão síncrona no loop.  
> **Data:** 2026-05-17  
> **Autor:** CTO (SOUL)  
> **Status:** Aprovado pelo usuário  
> **Plano substituído:** `.kimi/plans/adaptacao-sso-2fa.md` (arquitetura de script única descartada)

---

## 1. Visão Geral da Nova Arquitetura

O agente passa de **script que roda e termina** (executado via cron ou manualmente) para **serviço longo que permanece em execução durante toda a jornada de trabalho do operador**.

### Fluxo operacional aprovado

1. Operador clica **"Iniciar Agente"** no dashboard (ou executa atalho no desktop).
2. Agente abre Chrome **visível**, operador faz login no PJe e SISTJWEB (SSO + 2FA).
3. Agente salva **storage state** e entra em **loop infinito**:
   - Coleta novos processos do PJe
   - Preenche SISTJWEB
   - Verifica processos `status='aprovado'` → emite PDF → anexa no PJe → atualiza para `emitido`
   - Dorme 30 segundos
   - Volta ao início
4. Dashboard mostra status do agente em tempo real.
5. Processos aparecem no dashboard conforme são preenchidos.
6. Operador pode aprovar em tempo real (emite em ~30s) ou deixar e voltar depois.
7. No fim do dia, operador clica **"Parar Agente"** no dashboard.

### Diagrama de sequência

```
Operador     Dashboard    API        SQLite        Agente        PJe/SISTJWEB
   |             |          |           |             |               |
   |--"Iniciar"->|          |           |             |               |
   |             |--POST /iniciar------>|             |               |
   |             |          |--UPDATE comando='iniciar'               |
   |             |          |           |             |--(loop lê)    |
   |             |          |           |             |--status='autenticando'
   |             |          |           |             |--abre navegador VISÍVEL
   |             |          |           |             |<--login manual|
   |             |          |           |             |--salva storage state
   |             |          |           |             |--status='executando'
   |             |          |           |             |--coleta proc->|
   |             |          |           |             |<--lista-------|
   |             |          |           |             |--preenche--->|
   |             |          |           |             |<--ok---------|
   |             |          |           |<--UPDATE status='aguardando_aprovacao'
   |             |<--GET /status--------|           |               |
   |<--"Executando"          |           |             |               |
   |             |          |           |             |--status='dormindo'
   |             |          |           |             |--Event.wait(30s)
   |             |          |           |             |--status='executando'
   |             |          |           |             |--verifica aprovados
   |             |          |           |             |--emite PDF-->|
   |             |          |           |             |--anexa PJe-->|
   |             |          |           |<--UPDATE status='emitido'   |
   |             |          |           |             |               |
   |--"Parar"--->|          |           |             |               |
   |             |--POST /parar-------->|             |               |
   |             |          |--UPDATE comando='parar'                 |
   |             |          |           |             |--(lê comando) |
   |             |          |           |             |--status='parando'
   |             |          |           |             |--fecha browsers
   |             |          |           |             |--status='parado'
   |             |          |           |             |--exit         |
```

### Componentes e responsabilidades

| Componente | Onde roda | Responsabilidade |
|---|---|---|
| **Agente (serviço longo)** | Host nativo (fora do Docker) | Loop infinito, automação Playwright, leitura/escrita no SQLite, gerenciamento de sessão |
| **API (FastAPI)** | Container Docker | Receber comandos do frontend, escrever `comando` na tabela `agente_controle`, ler `status` para responder ao frontend |
| **Frontend (React)** | Container Docker (servido pelo nginx) | Exibir status do agente, botões Iniciar/Parar, fila de processos |
| **SQLite** | Arquivo `./dados/custas.db` (bind mount) | Única fonte de verdade para dados de processos e controle do agente. Compartilhado entre host (agente) e containers (API) |

---

## 2. Mudanças no Agente (Serviço Longo)

### 2.1 Loop principal e máquina de estados

O agente implementa uma **máquina de estados explícita** onde cada estado é processado em uma iteração do loop principal. Isso permite:
- Interrupção limpa a qualquer momento (graceful shutdown)
- Transição controlada para fallback de autenticação
- Recuperação automática de erros transitórios

#### Estados

```
parado → iniciando → autenticando → executando → dormindo → executando → ...
                                              ↓
                                        aguardando_login (sessão expirada)
                                              ↓
                                        autenticando → executando
                                              ↓
                                        erro (falha não recuperável)
                                              ↓
                                        executando (auto-recovery após sleep)
                                              ↓
                                        parando → parado
```

#### Transições de estado

| De | Para | Gatilho |
|---|---|---|
| `parado` | `autenticando` | `comando='iniciar'` lido do SQLite |
| `autenticando` | `executando` | Login bem-sucedido (storage state válido ou manual) |
| `autenticando` | `aguardando_login` | Storage state inválido/ausente — necessita login manual |
| `executando` | `dormindo` | Uma iteração completa (coleta + preenchimento + emissão) finalizada |
| `dormindo` | `executando` | `Event.wait(30)` expirou e `comando != 'parar'` |
| `executando` | `aguardando_login` | Sessão expirada DETECTADA durante processamento |
| `aguardando_login` | `autenticando` | Operador completou login no navegador visível |
| `aguardando_login` | `erro` | Timeout de 10 minutos sem login manual |
| `executando` / `dormindo` | `parando` | `comando='parar'` lido do SQLite ou sinal SIGINT/SIGTERM |
| `parando` | `parado` | Teardown completo (browsers fechados, recursos liberados) |
| `erro` | `executando` | Após sleep de 30s (auto-recovery) |

### 2.2 Como o agente detecta que foi "iniciado" pelo dashboard

1. A API recebe `POST /agente/iniciar` do frontend.
2. A API executa `UPDATE agente_controle SET comando='iniciar', atualizado_em=CURRENT_TIMESTAMP WHERE id=1`.
3. O agente, no início de cada iteração do loop, lê a tabela `agente_controle`.
4. Se `comando='iniciar'` e o status atual do agente é `parado`, o agente transiciona para `autenticando`.

**Importante:** o agente é quem escreve o `status`. A API escreve apenas o `comando`. Isso evita race conditions sobre "quem é a fonte da verdade do estado atual".

### 2.3 Como o agente detecta que foi "parado" pelo dashboard

1. A API recebe `POST /agente/parar`.
2. A API executa `UPDATE agente_controle SET comando='parar', atualizado_em=CURRENT_TIMESTAMP WHERE id=1`.
3. O agente lê `comando='parar'` no início da próxima iteração.
4. Define `self._should_stop = True` (via `threading.Event.set()`).
5. Ao final da iteração atual (ou imediatamente se estiver `dormindo`), transiciona para `parando`, executa teardown e termina.

### 2.4 Como o agente lida com sessão expirada DURANTE o loop

O decorador `retry_on_exception` (em `agente/src/modulos/retry.py`) já detecta sessão expirada e tenta reconectar. Com SSO+2FA, a reconexão programática falha.

**Nova abordagem:**

1. Durante qualquer operação Playwright, se `is_session_expired(page)` retornar `True`, o `retry_on_exception` **não tenta reconectar automaticamente** quando está no modo serviço longo. Em vez disso, lança `ReautenticacaoNecessariaError(sistema)`.
2. O loop principal captura essa exceção:
   - Fecha o browser headless atual do sistema afetado
   - Atualiza `agente_controle` para `status='aguardando_login'` com mensagem informativa
   - Na próxima iteração, o estado `aguardando_login` dispara `_autenticar_interativo()`
3. `_autenticar_interativo()`:
   - Abre navegador visível (`headless=False`)
   - Navega para a URL de login
   - Faz polling a cada 2 segundos verificando se o login foi bem-sucedido (via `verificar_sucesso_fn`)
   - Timeout de 10 minutos
   - Quando logado, salva storage state, fecha navegador visível, reabre headless
   - Atualiza status para `executando`

### 2.5 Graceful shutdown (Ctrl+C, sinal SIGTERM)

```python
import signal
import threading

class AgenteServico:
    def __init__(self):
        self._stop_event = threading.Event()

    def _handle_signal(self, signum, frame):
        self._stop_event.set()
        self._set_status('parando', f'Sinal {signum} recebido. Finalizando...')

    def run(self):
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

        while not self._stop_event.is_set():
            try:
                self._loop_iteration()
            except Exception as e:
                self._set_status('erro', str(e))
                self._stop_event.wait(timeout=30)  # interrompível

        self._cleanup()
        self._set_status('parado', 'Serviço encerrado.')

    def _loop_iteration(self):
        comando, status_db = self._ler_comando()

        if comando == 'parar' or self._stop_event.is_set():
            self._should_stop = True
            return

        if status_db == 'parado' and comando == 'iniciar':
            self._set_status('autenticando')
            return

        if status_db == 'autenticando':
            try:
                self._autenticar_todos()
                self._set_status('executando')
            except ReautenticacaoNecessariaError as e:
                self._set_status('aguardando_login', f'Sessão {e.sistema} expirada. Faça login no navegador.')
            return

        if status_db == 'aguardando_login':
            try:
                self._autenticar_interativo()
                self._set_status('executando')
            except TimeoutError:
                self._set_status('erro', 'Timeout aguardando login manual.')
            return

        if status_db == 'executando':
            try:
                self._processar_iteracao()
                self._set_status('dormindo')
            except ReautenticacaoNecessariaError as e:
                self._set_status('aguardando_login', f'Sessão {e.sistema} expirada durante execução.')
            except Exception as e:
                self._set_status('erro', str(e))
            return

        if status_db == 'dormindo':
            self._stop_event.wait(timeout=30)  # dorme 30s, interrompível
            if not self._stop_event.is_set():
                self._set_status('executando')
            return

        if status_db == 'erro':
            self._stop_event.wait(timeout=30)
            if not self._stop_event.is_set():
                self._set_status('executando')
            return

        # Estado desconhecido — espera curta
        self._stop_event.wait(timeout=5)
```

### 2.6 Novo entry point

```bash
# Execução no host
python -m agente.src.servico
```

O arquivo `agente/src/main.py` pode ser mantido como legado ou removido. Recomendação: renomear `main.py` para `pipeline.py` (contém as funções de processamento) e criar `servico.py` como novo entry point.

---

## 3. Comunicação Dashboard ↔ Agente via SQLite

### 3.1 Schema da tabela `agente_controle`

Adicionar ao `shared/sog_shared/schema.sql`:

```sql
CREATE TABLE IF NOT EXISTS agente_controle (
    id INTEGER PRIMARY KEY CHECK (id = 1),  -- sempre exatamente 1 linha
    comando TEXT NOT NULL DEFAULT 'parar',    -- iniciar | parar
    status TEXT NOT NULL DEFAULT 'parado',    -- parado | iniciando | autenticando | executando | dormindo | aguardando_login | erro | parando
    mensagem TEXT DEFAULT '',
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    pid INTEGER                               -- PID do processo agente no host
);
```

**Racional:**
- `CHECK (id = 1)` garante monorregistro. A aplicação sempre usa `id=1`.
- `comando` é escrito pela **API** (dashboard). Representa a intenção do operador.
- `status` é escrito pelo **agente**. Representa o estado real.
- `mensagem` é escrita pelo agente para comunicar ao operador (ex: "Aguardando login no PJe").
- `pid` permite ao dashboard inferir se o agente está vivo (mesmo que o timestamp esteja atualizado, o PID ajuda em diagnósticos).

### 3.2 Funções no pacote compartilhado `shared/sog_shared/db.py`

```python
def obter_controle_agente() -> Optional[Dict[str, Any]]:
    """Retorna o registro de controle do agente (id=1) ou None."""
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM agente_controle WHERE id = 1").fetchone()
        return dict(row) if row else None


def criar_ou_atualizar_controle_agente(
    comando: Optional[str] = None,
    status: Optional[str] = None,
    mensagem: Optional[str] = None,
    pid: Optional[int] = None,
) -> None:
    """
    Upsert na tabela agente_controle (id=1).
    Campos None são ignorados (mantêm valor atual).
    """
    with get_conn() as conn:
        row = conn.execute("SELECT id FROM agente_controle WHERE id = 1").fetchone()
        if row:
            campos = []
            vals = []
            if comando is not None:
                campos.append("comando = ?")
                vals.append(comando)
            if status is not None:
                campos.append("status = ?")
                vals.append(status)
            if mensagem is not None:
                campos.append("mensagem = ?")
                vals.append(mensagem)
            if pid is not None:
                campos.append("pid = ?")
                vals.append(pid)
            if campos:
                campos.append("atualizado_em = CURRENT_TIMESTAMP")
                conn.execute(
                    f"UPDATE agente_controle SET {', '.join(campos)} WHERE id = 1",
                    vals,
                )
                conn.commit()
        else:
            conn.execute(
                "INSERT INTO agente_controle (id, comando, status, mensagem, pid) VALUES (1, ?, ?, ?, ?)",
                (comando or 'parar', status or 'parado', mensagem or '', pid),
            )
            conn.commit()
```

### 3.3 Endpoints da API

**Novo arquivo: `api/src/rotas/agente.py`**

```python
"""
Rotas de controle do agente de automação.
A API escreve comandos (iniciar/parar); o agente lê e executa.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sog_shared import db
from auth import get_current_user
from limiter import limiter

router = APIRouter(prefix="/agente", tags=["agente"])


class AgenteStatusResponse(BaseModel):
    status: str
    mensagem: str
    atualizado_em: Optional[str] = None
    online: bool


class AgenteComandoResponse(BaseModel):
    message: str


@router.post("/iniciar", response_model=AgenteComandoResponse)
@limiter.limit("10/minute")
def iniciar_agente(
    request,  # type: ignore # required by slowapi
    user: str = Depends(get_current_user),
):
    db.criar_ou_atualizar_controle_agente(comando='iniciar')
    return {"message": "Comando 'iniciar' enviado ao agente."}


@router.post("/parar", response_model=AgenteComandoResponse)
@limiter.limit("10/minute")
def parar_agente(
    request,  # type: ignore # required by slowapi
    user: str = Depends(get_current_user),
):
    db.criar_ou_atualizar_controle_agente(comando='parar')
    return {"message": "Comando 'parar' enviado ao agente."}


@router.get("/status", response_model=AgenteStatusResponse)
def status_agente(user: str = Depends(get_current_user)):
    controle = db.obter_controle_agente()
    if not controle:
        return {
            "status": "desconhecido",
            "mensagem": "Agente não registrado. Execute o aplicativo no desktop.",
            "online": False,
        }

    online = False
    if controle.get("atualizado_em"):
        from datetime import datetime, timezone
        try:
            # SQLite pode retornar string no formato '2026-05-17 14:30:00'
            # ou com timezone. Tenta ambos.
            atualizado_str = controle["atualizado_em"]
            if isinstance(atualizado_str, str):
                if atualizado_str.endswith('Z'):
                    atualizado_str = atualizado_str[:-1] + '+00:00'
                try:
                    ultimo = datetime.fromisoformat(atualizado_str)
                except ValueError:
                    ultimo = datetime.strptime(atualizado_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            else:
                ultimo = atualizado_str

            agora = datetime.now(ultimo.tzinfo)
            diff = (agora - ultimo).total_seconds()
            online = diff < 90  # 90 segundos = tolerância para 1 ciclo + margem
        except Exception:
            pass

    return {
        "status": controle["status"],
        "mensagem": controle.get("mensagem", ""),
        "atualizado_em": controle.get("atualizado_em"),
        "online": online,
    }
```

### 3.4 Registro do router

Em `api/src/app.py`, adicionar:
```python
from rotas import agente
# ...
app.include_router(agente.router)
```

---

## 4. Autenticação com Storage State + Fallback Interativo

### 4.1 Visão geral

A autenticação é encapsulada em uma nova classe `AuthManager` que gerencia o ciclo de vida do browser Playwright e a persistência de sessão.

Cada cliente (PjeClient, SistjClient) instancia seu próprio `AuthManager` com um arquivo de storage state distinto.

### 4.2 AuthManager

**Novo arquivo: `agente/src/modulos/auth_manager.py`**

```python
"""
Gerenciador de autenticação Playwright com storage state e fallback interativo.
"""
import time
from pathlib import Path
from typing import Callable, Optional

from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext, TimeoutError as PlaywrightTimeout

from config import TIMEOUT_PADRAO
from utils.logger import info, erro, aviso


class ReautenticacaoNecessariaError(Exception):
    """Levantada quando a sessão expirou e requer login manual."""
    def __init__(self, sistema: str):
        self.sistema = sistema
        super().__init__(f"Reautenticação necessária no {sistema}")


class AuthManager:
    """
    Gerencia browser Playwright com:
    1. Carregamento de storage state (sessão reusável)
    2. Verificação de sessão ativa
    3. Fallback interativo (navegador visível) quando sessão expirou
    """

    def __init__(self, storage_path: Path, headless_default: bool = True):
        self.storage_path = storage_path
        self.headless_default = headless_default
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._playwright = None

    def iniciar(self, accept_downloads: bool = False):
        """Inicializa browser headless com storage state se disponível."""
        if self._playwright:
            return

        self._playwright = sync_playwright().start()
        self.browser = self._playwright.chromium.launch(headless=self.headless_default)

        context_kwargs = {
            "viewport": {"width": 1920, "height": 1080},
            "accept_downloads": accept_downloads,
        }
        if self.storage_path.exists():
            context_kwargs["storage_state"] = str(self.storage_path)

        self.context = self.browser.new_context(**context_kwargs)
        self.page = self.context.new_page()
        self.page.set_default_timeout(TIMEOUT_PADRAO)

    def verificar_e_autenticar(
        self,
        url: str,
        verificar_sucesso_fn: Callable[[Page], bool],
        accept_downloads: bool = False,
        interativo_timeout_ms: int = 600_000,  # 10 minutos
    ) -> bool:
        """
        Fluxo completo:
        1. Inicia browser headless (com storage state se existir)
        2. Navega para url e verifica sessão
        3. Se válida → retorna True
        4. Se expirada → fallback interativo (navegador visível)
        5. Após login manual → salva storage state → reabre headless → retorna True
        """
        self.iniciar(accept_downloads=accept_downloads)

        self.page.goto(url, wait_until="networkidle")
        self.page.wait_for_timeout(2000)

        if verificar_sucesso_fn(self.page):
            return True

        # Sessão expirada — fallback interativo
        self._fallback_interativo(url, verificar_sucesso_fn, interativo_timeout_ms)
        return True

    def _fallback_interativo(
        self,
        url: str,
        verificar_sucesso_fn: Callable[[Page], bool],
        timeout_ms: int,
    ):
        """Abre navegador visível, aguarda login manual, salva storage state."""
        sistema = "sistema"  # será sobrescrito por callers
        aviso(f"Sessão expirada. Abrindo navegador visível para reautenticação...")

        # Fecha headless atual
        self.fechar()

        # Abre visível
        self._playwright = sync_playwright().start()
        self.browser = self._playwright.chromium.launch(headless=False)
        self.context = self.browser.new_context(viewport={"width": 1920, "height": 1080})
        self.page = self.context.new_page()

        self.page.goto(url, wait_until="networkidle")
        info("Navegador visível aberto. Aguardando login manual...")

        # Polling a cada 2s verificando se logou
        inicio = time.time()
        timeout_sec = timeout_ms / 1000
        logado = False

        while time.time() - inicio < timeout_sec:
            try:
                self.page.wait_for_timeout(2000)
                if verificar_sucesso_fn(self.page):
                    logado = True
                    break
            except Exception:
                pass

        if not logado:
            self.fechar()
            raise TimeoutError("Tempo esgotado aguardando login manual")

        # Salva storage state
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.context.storage_state(path=str(self.storage_path))
        info(f"Storage state salvo em {self.storage_path}")

        # Fecha visível e reabre headless
        self.fechar()
        self.iniciar()

    def fechar(self):
        """Fecha context, browser e playwright de forma segura."""
        if self.context:
            try:
                self.context.close()
            except Exception:
                pass
            self.context = None
        if self.browser:
            try:
                self.browser.close()
            except Exception:
                pass
            self.browser = None
        if self._playwright:
            try:
                self._playwright.stop()
            except Exception:
                pass
            self._playwright = None
        self.page = None

    def __del__(self):
        self.fechar()
```

### 4.3 Modificações nos clientes

**`agente/src/modulos/playwright_client.py` — adaptação:**

```python
from modulos.auth_manager import AuthManager, ReautenticacaoNecessariaError

class PlaywrightClient:
    def __init__(self):
        self._auth: Optional[AuthManager] = None

    @property
    def page(self) -> Optional[Page]:
        return self._auth.page if self._auth else None

    @property
    def browser(self) -> Optional[Browser]:
        return self._auth.browser if self._auth else None

    def fechar(self):
        if self._auth:
            self._auth.fechar()

    def verificar_sessao(self) -> bool:
        if not self.page:
            return True
        from modulos.retry import is_session_expired
        return is_session_expired(self.page)

    def login(self) -> bool:
        raise NotImplementedError("Subclasses devem implementar login()")
```

**`agente/src/modulos/pje.py` — PjeClient adaptado:**

```python
from config import PJE_URL, PJE_ETIQUETA, STORAGE_STATE_PJE
from modulos.auth_manager import AuthManager

class PjeClient(PlaywrightClient):
    def __init__(self):
        super().__init__()
        self._auth = AuthManager(STORAGE_STATE_PJE, headless_default=HEADLESS)

    def garantir_autenticado(self) -> bool:
        """Verifica autenticação; se necessário, dispara fallback interativo."""
        return self._auth.verificar_e_autenticar(
            url=PJE_URL,
            verificar_sucesso_fn=self._esta_logado,
            accept_downloads=True,
        )

    def _esta_logado(self, page: Page) -> bool:
        """Retorna True se a página indicar que o usuário está logado no PJe."""
        # Extrair a lógica de verificação da função login() atual (linhas 288-343)
        # Reutilizar os mesmos indicadores e seletores genéricos
        ...
```

**`agente/src/modulos/sistjweb.py` — SistjClient adaptado:**

```python
from config import SISTJ_URL, STORAGE_STATE_SISTJ
from modulos.auth_manager import AuthManager

class SistjClient(PlaywrightClient):
    def __init__(self):
        super().__init__()
        self._auth = AuthManager(STORAGE_STATE_SISTJ, headless_default=HEADLESS)

    def garantir_autenticado(self) -> bool:
        return self._auth.verificar_e_autenticar(
            url=SISTJ_URL,
            verificar_sucesso_fn=self._esta_logado,
        )

    def _esta_logado(self, page: Page) -> bool:
        # Verifica se há elementos indicativos de login bem-sucedido
        # (ex: menu "Custas" visível, ou ausência de campos de login)
        ...
```

**`agente/src/config.py` — adições:**

```python
# Storage State
STORAGE_STATE_DIR = Path(os.getenv("STORAGE_STATE_DIR", str(Path.home() / ".sog" / "auth")))
STORAGE_STATE_PJE = Path(os.getenv("STORAGE_STATE_PJE", str(STORAGE_STATE_DIR / "pje_storage.json")))
STORAGE_STATE_SISTJ = Path(os.getenv("STORAGE_STATE_SISTJ", str(STORAGE_STATE_DIR / "sistj_storage.json")))
```

### 4.4 Sessão expirada durante o loop

O decorador `retry_on_exception` em `retry.py` precisa de uma pequena adaptação: quando `instance.verificar_sessao()` retornar `True` (expirada), em vez de chamar `instance.reconectar()` (que faz login programático e falhará), ele deve lançar `ReautenticacaoNecessariaError`.

**Modificação em `agente/src/modulos/retry.py`:**

```python
# NOVO: importar a exceção
from modulos.auth_manager import ReautenticacaoNecessariaError

# Dentro do decorator retry_on_exception, na seção de reconexão:
if instance and hasattr(instance, "verificar_sessao") and hasattr(instance, "page"):
    try:
        if instance.verificar_sessao():
            info(f"Sessão expirada em {func_name}...")
            # NOVO: se o cliente usa AuthManager (serviço longo), não tenta reconectar programaticamente
            if hasattr(instance, "_auth") and instance._auth is not None:
                # Lança exceção para o loop principal tratar com fallback interativo
                raise ReautenticacaoNecessariaError(instance.__class__.__name__)
            # LEGADO: tenta reconectar (mantido para compatibilidade)
            if hasattr(instance, "reconectar"):
                instance.reconectar()
    except ReautenticacaoNecessariaError:
        raise
    except Exception as recon_err:
        aviso(f"Erro ao verificar/reconectar em {func_name}: {recon_err}")
```

---

## 5. Emissão em Tempo Real

### 5.1 O que muda

- **`api/src/rotas/aprovacao.py`**: Remove `BackgroundTasks` e `_disparar_emissao`. Apenas atualiza `status='aprovado'`.
- **`agente/src/modulos/emissor.py`**: Recebe clients já instanciados (não cria novos). Chama `garantir_autenticado()` em vez de `login()`.
- **`agente/src/servico.py`**: A cada iteração do loop, após preencher novos processos, chama `emitir_pendentes(self.sistj, self.pje)`.

### 5.2 Emissor adaptado

```python
# agente/src/modulos/emissor.py (modificado)
from typing import Optional
from sog_shared import db
from utils.logger import info, erro
from modulos.sistjweb import SistjClient
from modulos.pje import PjeClient


def emitir_e_anexar(processo_id: int, sistj: SistjClient, pje: PjeClient) -> bool:
    processo = db.obter_dados_processo(processo_id)
    if not processo:
        erro(f"Dados do processo {processo_id} não encontrados.")
        return False

    numero = processo.get("numero", "")
    numero_sem_mascara = processo.get("numero_sem_mascara", "")

    try:
        # SISTJWEB — já autenticado (garantir_autenticado é no-op se sessão viva)
        if not sistj.garantir_autenticado():
            raise RuntimeError("Falha na autenticação SISTJWEB")
        caminho_pdf = sistj.gravar_e_aprovar(numero_sem_mascara)

        # PJe
        if not pje.garantir_autenticado():
            raise RuntimeError("Falha na autenticação PJE")
        pje.anexar_demonstrativo(numero, caminho_pdf)

        db.atualizar_status(processo_id, "emitido")
        db.registrar_log(processo_id, "emissao", "ok", f"Demonstrativo: {caminho_pdf}")
        info(f"Processo {numero} emitido e anexado com sucesso.")
        return True
    except Exception as e:
        db.atualizar_status(processo_id, "erro", str(e))
        db.registrar_log(processo_id, "emissao", "erro", str(e))
        erro(f"Erro na emissão do processo {numero}: {e}")
        return False


def emitir_pendentes(sistj: SistjClient, pje: PjeClient) -> None:
    """Processa todos os processos com status='aprovado'."""
    from sog_shared.db import listar_aprovados
    pendentes = listar_aprovados()
    if not pendentes:
        return

    info(f"Processando {len(pendentes)} emissões pendentes...")
    for proc in pendentes:
        emitir_e_anexar(proc["id"], sistj, pje)
```

### 5.3 Função no banco para listar aprovados

Em `shared/sog_shared/db.py`:

```python
def listar_aprovados(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM processos WHERE status = 'aprovado' ORDER BY atualizado_em LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]
```

### 5.4 API de aprovação simplificada

```python
# api/src/rotas/aprovacao.py (modificado)
@router.post("/aprovar/{processo_id}", response_model=AprovacaoResponse)
@limiter.limit("10/minute")
def aprovar_processo(
    processo_id: int,
    request: Request,
    user: str = Depends(get_current_user),
):
    with db.get_conn() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT status FROM processos WHERE id = ?", (processo_id,)
        ).fetchone()
        if not row:
            conn.rollback()
            raise HTTPException(status_code=404, detail="Processo não encontrado")
        if row["status"] != "aguardando_aprovacao":
            conn.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Processo não está aguardando aprovação",
            )

        conn.execute(
            "UPDATE processos SET status = 'aprovado', atualizado_em = CURRENT_TIMESTAMP WHERE id = ?",
            (processo_id,),
        )
        conn.execute(
            "INSERT INTO log_execucao (processo_id, etapa, status, mensagem) VALUES (?, ?, ?, ?)",
            (processo_id, "aprovacao", "ok", f"Aprovado por {user}"),
        )
        conn.commit()

    return {"message": "Aprovação registrada. O agente processará a emissão em breve."}
```

---

## 6. Status do Agente no Dashboard

### 6.1 Componente de status

**Novo arquivo: `frontend/src/components/agente/AgenteStatusBar.tsx`**

```typescript
import { useEffect, useState, useCallback } from 'react'
import api from '../../lib/api'
import { ENDPOINTS } from '../../lib/endpoints'
import Button from '../ui/Button'

type AgenteStatus =
  | 'parado'
  | 'iniciando'
  | 'autenticando'
  | 'executando'
  | 'dormindo'
  | 'aguardando_login'
  | 'erro'
  | 'parando'
  | 'desconhecido'

const STATUS_CONFIG: Record<string, { cor: string; label: string }> = {
  executando: { cor: 'bg-green-500', label: 'Executando' },
  dormindo: { cor: 'bg-green-400', label: 'Executando (pausa)' },
  autenticando: { cor: 'bg-blue-500', label: 'Autenticando' },
  aguardando_login: { cor: 'bg-yellow-500', label: 'Aguardando login' },
  parado: { cor: 'bg-gray-400', label: 'Parado' },
  desconhecido: { cor: 'bg-gray-300', label: 'Offline' },
  erro: { cor: 'bg-red-500', label: 'Erro' },
  iniciando: { cor: 'bg-blue-400', label: 'Iniciando' },
  parando: { cor: 'bg-orange-500', label: 'Parando' },
}

export default function AgenteStatusBar() {
  const [status, setStatus] = useState<AgenteStatus>('desconhecido')
  const [mensagem, setMensagem] = useState('')
  const [online, setOnline] = useState(false)
  const [loading, setLoading] = useState(false)

  const fetchStatus = useCallback(async () => {
    try {
      const res = await api.get(ENDPOINTS.AGENTE_STATUS)
      setStatus(res.data.status)
      setMensagem(res.data.mensagem)
      setOnline(res.data.online)
    } catch {
      setStatus('desconhecido')
      setOnline(false)
    }
  }, [])

  useEffect(() => {
    fetchStatus()
    const interval = setInterval(fetchStatus, 5000)
    return () => clearInterval(interval)
  }, [fetchStatus])

  async function handleIniciar() {
    setLoading(true)
    try {
      await api.post(ENDPOINTS.AGENTE_INICIAR)
      await fetchStatus()
    } finally {
      setLoading(false)
    }
  }

  async function handleParar() {
    setLoading(true)
    try {
      await api.post(ENDPOINTS.AGENTE_PARAR)
      await fetchStatus()
    } finally {
      setLoading(false)
    }
  }

  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.desconhecido
  const podeIniciar = ['parado', 'desconhecido', 'erro'].includes(status)
  const podeParar = ['executando', 'dormindo', 'autenticando', 'aguardando_login', 'iniciando'].includes(status)

  return (
    <div className="flex flex-wrap items-center gap-4 p-3 bg-card border rounded-lg mb-6">
      <div className="flex items-center gap-2">
        <span className={`w-3 h-3 rounded-full ${cfg.cor} ${online ? '' : 'opacity-40'}`} />
        <span className="font-medium">{cfg.label}</span>
        {mensagem && (
          <span className="text-sm text-muted-foreground">— {mensagem}</span>
        )}
      </div>
      <div className="ml-auto flex gap-2">
        <Button onClick={handleIniciar} disabled={!podeIniciar || loading}>
          ▶ Iniciar Agente
        </Button>
        <Button onClick={handleParar} disabled={!podeParar || loading} variant="outline">
          ⏹ Parar Agente
        </Button>
      </div>
    </div>
  )
}
```

### 6.2 Integração na página Fila

Em `frontend/src/pages/Fila.tsx`, adicionar antes do `<BuscaProcesso>`:

```tsx
import AgenteStatusBar from '../components/agente/AgenteStatusBar'
// ...
<div className="space-y-8">
  <AgenteStatusBar />
  <BuscaProcesso valor={busca} onChange={setBusca} />
  {/* ... resto */}
</div>
```

### 6.3 Endpoints no frontend

Em `frontend/src/lib/endpoints.ts`, adicionar:

```typescript
export const ENDPOINTS = {
  // ... existentes ...
  AGENTE_INICIAR: '/agente/iniciar',
  AGENTE_PARAR: '/agente/parar',
  AGENTE_STATUS: '/agente/status',
} as const
```

---

## 7. Plano de Implementação Sequencial

### Fase 1 — Agente como Serviço Longo + Comunicação SQLite + API + Dashboard

#### Arquivos a criar / modificar / deletar

| Ação | Caminho | Motivo |
|---|---|---|
| **Criar** | `agente/src/servico.py` | Entry point do serviço longo; loop principal + máquina de estados + graceful shutdown |
| **Modificar** | `shared/sog_shared/schema.sql` | Adicionar tabela `agente_controle` |
| **Modificar** | `shared/sog_shared/db.py` | Adicionar `obter_controle_agente`, `criar_ou_atualizar_controle_agente`, `listar_aprovados` |
| **Criar** | `api/src/rotas/agente.py` | Endpoints `/agente/iniciar`, `/agente/parar`, `/agente/status` |
| **Modificar** | `api/src/app.py` | Registrar router `agente` |
| **Modificar** | `api/src/schemas.py` | Adicionar `AgenteStatusResponse`, `AgenteComandoResponse` |
| **Criar** | `frontend/src/components/agente/AgenteStatusBar.tsx` | Barra de status com bolinha, mensagem e botões |
| **Modificar** | `frontend/src/lib/endpoints.ts` | Adicionar endpoints do agente |
| **Modificar** | `frontend/src/pages/Fila.tsx` | Incluir `<AgenteStatusBar />` |
| **Renomear** | `agente/src/main.py` → `agente/src/pipeline.py` | Preservar lógica de processamento; renomear para não conflitar com novo entry point |
| **Deletar** | `agente/crontab` | O cron não é mais necessário no modelo de serviço longo |
| **Criar** | `run_agente.sh` / `run_agente.bat` | Script wrapper para execução no host (ativa venv, seta PYTHONPATH, roda serviço) |

#### Interfaces e Contratos

**`agente/src/servico.py` — classe principal:**

```python
class AgenteServico:
    def __init__(self):
        self._stop_event = threading.Event()
        self.pje = PjeClient()
        self.sistj = SistjClient()

    def run(self) -> None:
        """Entry point do serviço longo."""

    def _loop_iteration(self) -> None:
        """Uma iteração da máquina de estados."""

    def _processar_iteracao(self) -> None:
        """Coleta, preenche e emite em um ciclo."""

    def _autenticar_todos(self) -> None:
        """Autentica PJe e SISTJWEB (pode disparar fallback visível)."""

    def _autenticar_interativo(self) -> None:
        """Chamado quando status='aguardando_login'."""

    def _ler_comando(self) -> Tuple[str, str]:
        """Lê comando e status atual do SQLite. Retorna (comando, status)."""

    def _set_status(self, status: str, mensagem: str = "") -> None:
        """Atualiza status do agente no SQLite."""

    def _cleanup(self) -> None:
        """Fecha browsers e libera recursos."""
```

**`shared/sog_shared/db.py` — novas funções:**

```python
def obter_controle_agente() -> Optional[Dict[str, Any]]: ...
def criar_ou_atualizar_controle_agente(...) -> None: ...
def listar_aprovados(limit=100, offset=0) -> List[Dict[str, Any]]: ...
```

#### Critérios de Aceite Mensuráveis

- [ ] Executar `python -m agente.src.servico` inicia o serviço, cria registro em `agente_controle` com `status='parado'`, e entra em loop aguardando comando.
- [ ] Clicar "Iniciar Agente" no dashboard faz `POST /agente/iniciar`. A API atualiza `comando='iniciar'` no SQLite.
- [ ] O agente lê o comando na próxima iteração, transiciona para `autenticando`, e abre navegador visível (primeira execução).
- [ ] Após login manual, o agente transiciona para `executando`, processa processos, depois `dormindo`, aguarda 30s, e volta a `executando`.
- [ ] Clicar "Parar Agente" faz `POST /agente/parar`. O agente lê, transiciona para `parando`, fecha browsers, e para com `status='parado'`.
- [ ] Pressionar `Ctrl+C` (SIGINT) durante qualquer estado faz o agente terminar graciosamente: fecha browsers e atualiza `status='parado'`.
- [ ] O frontend exibe a barra de status na página Fila com bolinha de cor correta conforme o estado.
- [ ] Se o agente não está rodando, o dashboard mostra "Offline" (bolinha cinza).
- [ ] O SQLite mantém apenas 1 linha na tabela `agente_controle` (testar tentativa de INSERT com id=2 → deve falhar).

---

### Fase 2 — Autenticação Storage State + Fallback Interativo

#### Arquivos a criar / modificar / deletar

| Ação | Caminho | Motivo |
|---|---|---|
| **Criar** | `agente/src/modulos/auth_manager.py` | Gerenciador de storage state e fallback interativo |
| **Modificar** | `agente/src/config.py` | Adicionar `STORAGE_STATE_DIR`, `STORAGE_STATE_PJE`, `STORAGE_STATE_SISTJ` |
| **Modificar** | `agente/src/modulos/playwright_client.py` | Integrar `AuthManager`; expor `page`/`browser` via properties |
| **Modificar** | `agente/src/modulos/pje.py` | Substituir `login()` por `garantir_autenticado()` usando `AuthManager` |
| **Modificar** | `agente/src/modulos/sistjweb.py` | Substituir `login()` por `garantir_autenticado()` usando `AuthManager` |
| **Modificar** | `agente/src/modulos/retry.py` | Detectar `AuthManager` e lançar `ReautenticacaoNecessariaError` em vez de tentar reconexão programática |
| **Modificar** | `agente/src/modulos/emissor.py` | Receber clients instanciados; chamar `garantir_autenticado()` em vez de `login()` |
| **Modificar** | `.env.agente` | Adicionar variáveis de storage state (opcional, com defaults para `~/.sog/auth/`) |

#### Interfaces e Contratos

**`agente/src/modulos/auth_manager.py`:**

```python
class ReautenticacaoNecessariaError(Exception):
    sistema: str

class AuthManager:
    def __init__(self, storage_path: Path, headless_default: bool = True): ...
    def iniciar(self, accept_downloads: bool = False) -> None: ...
    def verificar_e_autenticar(url, verificar_sucesso_fn, accept_downloads, interativo_timeout_ms) -> bool: ...
    def _fallback_interativo(url, verificar_sucesso_fn, timeout_ms) -> None: ...
    def fechar(self) -> None: ...
```

**`agente/src/modulos/pje.py`:**

```python
class PjeClient(PlaywrightClient):
    def __init__(self): ...
    def garantir_autenticado(self) -> bool: ...
    def _esta_logado(self, page: Page) -> bool: ...
    # demais métodos (coletar_lista_processos, coletar_documentos, anexar_demonstrativo) inalterados
```

#### Critérios de Aceite Mensuráveis

- [ ] Primeira execução (sem storage state): navegador visível abre para PJe, operador loga, agente salva `~/.sog/auth/pje_storage.json`. Mesmo para SISTJWEB.
- [ ] Segunda execução: agente carrega storage state, navega para PJe/SISTJWEB, confirma que está logado sem abrir navegador visível.
- [ ] Quando a sessão expira durante o loop, o agente atualiza `status='aguardando_login'` no SQLite, abre navegador visível, e aguarda login.
- [ ] O operador vê no dashboard a mensagem "Aguardando login no PJe" (ou SISTJWEB) com bolinha amarela.
- [ ] Após login manual durante o loop, o agente salva novo storage state, fecha navegador visível, e continua o loop.
- [ ] Timeout de 10 minutos no fallback: se operador não logar, agente vai para `status='erro'`.
- [ ] Nenhum login programático (usuário/senha hardcoded) é mais executado.

---

### Fase 3 — Correção CR-002 (Escaping CSS)

> **Nota:** Esta fase é idêntica ao plano anterior (`adaptacao-sso-2fa.md` Fase 2). Reproduzida aqui para completude.

#### Arquivos a criar / modificar / deletar

| Ação | Caminho | Motivo |
|---|---|---|
| **Criar** | `agente/src/modulos/css_escape.py` | Extrair `escape_for_css` para módulo utilitário compartilhado |
| **Modificar** | `agente/src/modulos/pje.py` | Importar de `css_escape`; auditar todos os seletores dinâmicos |
| **Modificar** | `agente/src/modulos/sistjweb.py` | Importar de `css_escape`; substituir `.format()` em `RADIO_ITEM_CALCULO` por f-strings com escape |
| **Modificar** | `agente/src/modulos/selectors.py` | Documentar templates como INSEGUROS; refatorar para funções geradoras se usados |

#### Critérios de Aceite Mensuráveis

- [ ] `escape_for_css` possui testes unitários cobrindo: string vazia, aspas simples, aspas duplas, backslash, string comum, múltiplos caracteres especiais.
- [ ] Zero ocorrências de `f"...{variavel}..."` ou `.format()` em seletores CSS sem `escape_for_css` em `agente/src/modulos/`.
- [ ] `selectors.py` não expõe templates com placeholders `{...}` como constantes globais (se necessário, são funções).

---

### Fase 4 — Integração de Custas Iniciais do PDF no Payload SISTJWEB

> **Nota:** Esta fase é idêntica em objetivo ao plano anterior, mas integrada no loop do serviço longo.

#### Arquivos a criar / modificar / deletar

| Ação | Caminho | Motivo |
|---|---|---|
| **Modificar** | `agente/src/modulos/pje.py` | Adicionar `baixar_documento_pdf(doc_id, caminho_destino)` |
| **Modificar** | `agente/src/pipeline.py` (ex-main.py) | Extrair PDFs de guias de custas; integrar `extrair_custas_iniciais` no payload |
| **Modificar** | `agente/src/pipeline.py` `_construir_payload` | Converter `custas_iniciais` em entradas na lista `custas_pagas` |

#### Critérios de Aceite Mensuráveis

- [ ] Quando um processo possui documento do tipo "Comprovante de Pagamento de Custas" ou "Guia", o agente baixa o PDF e extrai os valores via `extrair_texto_pdf`.
- [ ] O campo `custas_pagas` no payload do SISTJWEB contém, no mínimo, uma entrada com `data`, `valor` e `numero_guia` provenientes das custas iniciais.
- [ ] Se o PDF for scanned (`scanned=True`), o agente registra log de aviso e não tenta preencher custas iniciais.
- [ ] Se não houver guia de custas no processo, o payload continua funcionando normalmente.

---

### Fase 5 — Mapeamento de Regras para Criminal, Família, Fazenda Pública

> **Nota:** Esta fase é idêntica ao plano anterior.

#### Arquivos a criar / modificar / deletar

| Ação | Caminho | Motivo |
|---|---|---|
| **Modificar** | `agente/src/regras.py` | Preencher `familia`, `fazenda_publica`, `criminal` com regras validadas pela contadora |
| **Criar** | `docs/regras_custas_tjdft.md` | Documentação das regras por área, com fonte jurídica |

#### Critérios de Aceite Mensuráveis

- [ ] `regras.py` contém pelo menos uma regra não-vazia para `familia`, `fazenda_publica` e `criminal`.
- [ ] Teste com pelo menos 1 processo real de cada área: o pipeline preenche a planilha SISTJWEB sem cair em `pendente_manual`.
- [ ] `docs/regras_custas_tjdft.md` documenta a fonte de cada regra.
- [ ] Se uma área não tiver regra mapeada, continua caindo graciosamente em `pendente_manual`.

---

## 8. Riscos e Mitigações

| Risco | Prob. | Impacto | Mitigação |
|---|---|---|---|
| **Agente crasha e fica offline** | Média | Alto | O dashboard detecta `online=false` após 90s. O operador reinicia manualmente via atalho no desktop. Futuramente: watchdog/script de restart. |
| **Sessão expira durante processamento de um processo** | Média | Alto | `retry.py` detecta, lança `ReautenticacaoNecessariaError`, loop pausa em `aguardando_login`. O processo em andamento será reprocessado na próxima iteração (status volta para `pendente` ou fica como estava). |
| **Operador não está na máquina quando sessão expira** | Média | Médio | Timeout de 10 minutos no fallback. Após timeout, agente vai para `erro`. Operador vê mensagem no dashboard quando voltar. |
| **SQLite race condition entre agente e API** | Baixa | Alto | WAL mode já ativo. Ambos usam `BEGIN IMMEDIATE`. `busy_timeout=5000`. A tabela `agente_controle` tem escrita unidirecional (API escreve `comando`, agente escreve `status`), minimizando conflitos. |
| **Consumo de memória do Chrome ao longo de horas** | Média | Médio | O agente reabre browsers apenas quando necessário (fallback). Headless consome menos RAM. Se necessário, adicionar restart periódico dos browsers (não implementado nesta wave). |
| **Playwright detectado como bot** | Baixa | Alto | Login é feito pelo operador em navegador visível (interação humana real). Durante automação, mantém `headless=True` (padrão Playwright) e evita ações rápidas. |
| **Múltiplas instâncias do agente rodando simultaneamente** | Baixa | Alto | O campo `pid` permite identificar. O dev pode adicionar lock file (`~/.sog/agente.lock`) como melhoria futura. Para o MVP, documentar que só deve haver uma instância. |
| **Mapeamento de regras judiciais incorreto** | Média | Alto | Nunca inventar regras. Validar com contadora. Manter fallback `pendente_manual`. |

---

## 9. Decisões de Baixa Reversibilidade

### D1. Arquitetura de serviço longo (daemon)

> **⚠️ BAIXA REVERSIBILIDADE**
>
> O agente deixa de ser um script de execução única e passa a ser um processo longo. Isso muda fundamentalmente como ele é operado (não mais cron, não mais "rodar e esquecer").
>
> **Rollback:** Restaurar `main.py` como entry point principal e recriar `agente/crontab`. Reverter `servico.py` para um wrapper que roda uma única iteração e termina.

### D2. Comunicação via SQLite (tabela `agente_controle`)

> **⚠️ BAIXA REVERSIBILIDADE**
>
> O dashboard e o agente comunicam via banco de dados, não via HTTP/WebSocket nem fila de mensagens. Isso é simples mas acopla a comunicação ao schema do banco.
>
> **Rollback:** Reescrever toda a camada de comunicação para HTTP (agente expõe servidor HTTP) ou WebSocket. Requer mudanças em agente, API e frontend.

### D3. Emissão síncrona no loop do agente

> **⚠️ BAIXA REVERSIBILIDADE**
>
> A emissão pós-aprovação deixa de ser assíncrona (BackgroundTasks) ou em script separado (`emitir_pendentes.py`) e passa a ser parte síncrona do loop do agente. Isso significa que um processo aprovado só é emitido quando o agente passar por essa fase do loop (até 30s de delay).
>
> **Rollback:** Reintroduzir `BackgroundTasks` na API (mas isso requer Playwright no container API, que foi descartado) ou reintroduzir `emitir_pendentes.py` como script separado.

### D4. Agente fora do Docker (operação no host)

> **⚠️ BAIXA REVERSIBILIDADE** (já documentada no MEMORY.md)
>
> Mantida deste plano. O agente roda no host nativo para acesso ao display e Chrome visível.
>
> **Rollback:** Restaurar serviço `agente` no `docker-compose.yml` e resolver autenticação via outro mecanismo (ex: conexão a Chrome remoto).

---

## 10. Checklist de Execução para o Desenvolvedor

### Fase 1
- [ ] `agente/src/servico.py` criado com `AgenteServico` completo (loop, estados, signals, cleanup)
- [ ] `shared/sog_shared/schema.sql` atualizado com `agente_controle`
- [ ] `shared/sog_shared/db.py` com funções de controle do agente
- [ ] `api/src/rotas/agente.py` com endpoints `/iniciar`, `/parar`, `/status`
- [ ] `api/src/app.py` registrando router do agente
- [ ] `frontend/src/components/agente/AgenteStatusBar.tsx` funcionando com polling 5s
- [ ] `frontend/src/pages/Fila.tsx` incluindo a barra de status
- [ ] Teste manual: iniciar serviço → dashboard mostra "Parado" → clicar Iniciar → agente processa → clicar Parar → agente para
- [ ] Teste Ctrl+C: serviço termina graciosamente e atualiza status para 'parado'

### Fase 2
- [ ] `agente/src/modulos/auth_manager.py` criado e testado
- [ ] `PjeClient` e `SistjClient` usando `garantir_autenticado()`
- [ ] Primeiro login manual salva storage state em `~/.sog/auth/`
- [ ] Segunda execução reutiliza storage state sem interação
- [ ] Sessão expirada durante loop dispara `aguardando_login` e navegador visível
- [ ] `retry.py` lança `ReautenticacaoNecessariaError` em vez de tentar reconexão programática

### Fase 3
- [ ] `agente/src/modulos/css_escape.py` criado com testes unitários
- [ ] Zero seletores interpolados sem escaping

### Fase 4
- [ ] `pje.py` possui `baixar_documento_pdf()`
- [ ] Custas iniciais integradas no payload do SISTJWEB
- [ ] Teste com 3 processos reais (com guia, sem guia, scanned)

### Fase 5
- [ ] Regras coletadas da contadora
- [ ] `regras.py` populado e testado
- [ ] `docs/regras_custas_tjdft.md` documentado

### Finalização
- [ ] `MEMORY.md` atualizado com decisões arquiteturais deste plano
- [ ] `.kimi/plans/agente-servico-longo.md` marcado como concluído
