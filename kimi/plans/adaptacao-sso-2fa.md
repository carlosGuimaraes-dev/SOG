# Plano Técnico — Adaptação a SSO Microsoft + 2FA e Operação Local

> **Escopo:** Adaptar o pipeline SOG para operação local com autenticação humana inicial (SSO Microsoft + Microsoft Authenticator 2FA), corrigir gaps técnicos identificados e expandir regras de custas.  
> **Data:** 2026-05-17  
> **Autor:** CTO (SOUL)  
> **Status:** Draft → Aguardando aprovação CEO

---

## 1. Visão Geral da Solução

O acesso ao PJe e SISTJWEB do TJDFT migrou para SSO Microsoft com 2FA via Microsoft Authenticator, tornando o login programático impossível (a app não expõe secret TOTP). O sistema passa a operar em modo **local** (máquina do operador), com autenticação humana inicial e reutilização de sessão via **Playwright Storage State**.

A arquitetura evolui de "automação headless em VPS" para "agente local com sessão pré-autenticada + API/frontend em Docker". A emissão pós-aprovação, hoje quebrada por falta de Playwright no container API, é corrigida migrando a lógica de emissão para o agente via fila baseada em status do banco.

As cinco entregas são:
1. **Autenticação adaptada** — storage state persistente + fallback interativo
2. **Correção CR-002** — auditoria e hardening de seletores CSS dinâmicos
3. **Integração de custas iniciais** — usar dados extraídos do PDF no payload SISTJWEB
4. **Fila de emissão pós-aprovação** — remover emissão da API; agente consome fila
5. **Regras de custas para Criminal, Família, Fazenda Pública** — mapeamento judicial

---

## 2. Análise das Abordagens de Autenticação

### A) Playwright `connect_over_cdp` → Chrome já aberto pelo usuário

**Mecanismo:** O operador inicia o Chrome com `--remote-debugging-port=9222`. O Playwright conecta via `chromium.connect_over_cdp("http://localhost:9222")` e automatiza a instância existente.

| Dimensão | Avaliação |
|---|---|
| **Prós** | Usa o perfil do usuário (cookies, extensões, histórico). Sessão do SSO já ativa se o usuário navegou manualmente. |
| **Contras** | Requer iniciar Chrome com flag especial (difícil para operador não-técnico). Conflito com instâncias normais do Chrome. Em Windows/Mac, o Chrome pode recusar múltiplas instâncias com o mesmo perfil. Detecção de automação pelo SSO pode forçar reautenticação. |
| **Complexidade** | Média — lidar com perfis, portas, teardown seguro. |
| **Robustez com SSO+2FA** | Média — depende do perfil do usuário estar logado no IdP. Se o cookie de sessão do Microsoft expirar, não há fallback automático. |
| **UX do operador** | Ruim — precisa saber iniciar Chrome com flag de debug. Erros são técnicos e difíceis de diagnosticar. |

**Veredicto:** Descartada. UX inaceitável para operador não-técnico; fragilidade com perfis do Chrome.

---

### B) Storage State Persistente → login manual uma vez, reutiliza cookies/session

**Mecanismo:** Após login manual do operador, o Playwright salva o estado do contexto (`context.storage_state()`) em arquivo JSON. Execuções futuras carregam esse estado (`browser.new_context(storage_state=...)`), reutilizando cookies, localStorage e sessionStorage.

| Dimensão | Avaliação |
|---|---|
| **Prós** | API nativa do Playwright. Funciona com qualquer navegador (Chromium, Firefox, WebKit). Não requer flags especiais do Chrome. Estado portável entre execuções. |
| **Contras** | Sessão do SSO Microsoft expira (tipicamente 8–24h). Quando expirar, é necessário login manual novamente. |
| **Complexidade** | Baixa — ~30 linhas de código para salvar/carregar. |
| **Robustez com SSO+2FA** | Alta — o operador faz o fluxo completo de SSO+2FA uma vez; o Playwright reutiliza o estado de sessão. Se o IdP aceitar o cookie de sessão, funciona transparentemente. |
| **UX do operador** | Excelente — abre navegador, faz login normalmente, fecha. O sistema roda sozinho nas próximas horas. |

**Veredicto:** Forte candidata. É a base da solução recomendada.

---

### C) Modo "Espera Interativa" → abre navegador, pausa para usuário logar, depois executa

**Mecanismo:** O script abre o navegador visível (`headless=False`), navega para a URL de login, exibe uma mensagem no terminal (e.g., "Faça login no navegador e pressione ENTER...") e bloqueia em `input()`. Após o operador confirmar, o script continua.

| Dimensão | Avaliação |
|---|---|
| **Prós** | Extremamente simples de implementar. Não depende de mecanismos de persistência. Funciona sempre que o operador está presente. |
| **Contras** | Bloqueia a execução. Impossível de usar com cron. A cada execução (hora em hora), o operador precisa interagir. Não escala nem mesmo para dezenas de processos. |
| **Complexidade** | Baixíssima. |
| **Robustez com SSO+2FA** | Alta — o operador faz login manual a cada vez. |
| **UX do operador** | Péssima para uso recorrente. Viável apenas para testes ou execução esporádica. |

**Veredicto:** Descartada como solução primária. Útil apenas como fallback.

---

### D) Modo Híbrido — Storage State + Detecção de Expiração + Re-prompt

**Mecanismo:** Primariamente usa **Storage State (B)**. O agente, ao iniciar, tenta carregar o estado salvo e verifica se a sessão ainda é válida (navega para URL, verifica se há redirecionamento para login). Se a sessão estiver válida, prossegue automaticamente. Se expirou, cai para modo interativo (C): abre navegador visível, pede login manual, e salva o novo estado.

| Dimensão | Avaliação |
|---|---|
| **Prós** | Combina a UX excelente de (B) com a robustez de (C). O operador só é incomodado quando a sessão expira (1x ao dia ou menos). |
| **Contras** | Mais complexo de implementar (precisa de máquina de estados: verificar → reutilizar ou reprompt → salvar). |
| **Complexidade** | Média — requer classe gerenciadora de sessão com fallback. |
| **Robustez com SSO+2FA** | Muito alta — cobre tanto o caso feliz (sessão viva) quanto o caso de expiração. |
| **UX do operador** | Excelente — autonomia na maioria das execuções; intervenção humana apenas quando necessário. |

**Veredicto:** **Abordagem vencedora.**

---

## 3. Recomendação da Abordagem Vencedora

**Implementar o Modo Híbrido (D) com Storage State como mecanismo primário.**

### Justificativa Técnica

1. **SSO Microsoft + 2FA impossibilita qualquer automação programática** de login. O operador humano é um componente obrigatório do sistema.
2. **Operação local** significa que o operador está fisicamente presente na máquina. Um login manual uma vez por dia (ou até por semana, dependendo do TTL do cookie de sessão do TJDFT/IdP) é aceitável.
3. **Storage State é a API nativa e mais confiável do Playwright** para persistir sessões. Não depende de flags do Chrome nem de perfis de usuário.
4. **Fallback interativo** garante que o sistema nunca fique completamente bloqueado por expiração de sessão. O operador recebe uma janela do navegador, faz login normalmente, e o sistema continua.
5. **Menor risco de detecção como bot** — o operador faz o login em um navegador visível, com interações humanas reais (clique no link de SSO, aprovação no app do celular), o que reduz a chance de desafios CAPTCHA ou bloqueios por comportamento automatizado.

### Decisão de Baixa Reversibilidade

> ⚠️ **ARQUITETURA DE DEPLOY: Agente fora do Docker**
> 
> Para operação local com navegador visível e acesso ao filesystem do host (onde o storage state será salvo), o agente passa a rodar **diretamente no host** (Python venv), enquanto API e frontend permanecem em containers Docker.
> 
> **Justificativa:** Rodar o agente dentro de um container com X11 forwarding ou VNC é tecnicamente possível, mas adiciona complexidade desnecessária para um operador não-técnico. Rodar no host simplifica: o operador vê o Chrome normalmente, o storage state fica em `~/.sog/auth/`, e o acesso ao display é nativo.
> 
> **Impacto:** O `docker-compose.yml` perde o serviço `agente`. O SQLite continua compartilhado via `./dados/custas.db` (bind mount). O `docker-compose.dev.yml` pode manter o agente em container para desenvolvimento, mas com `network_mode: host` ou similar.
> 
> **Rollback:** Restaurar o serviço `agente` no `docker-compose.yml` e mover as credenciais de volta para `.env.agente` (reversível, mas requer alteração em múltiplos arquivos).

---

## 4. Mudanças Arquiteturais no Fluxo Atual

### 4.1 Como fica o `main.py` (hoje roda via cron)

O `main.py` continua sendo o entry point do agente. O cron pode continuar existindo, mas o comportamento muda:

```
rodar():
  1. init_config()
  2. db.init_db()
  3. pje = PjeClient()
  4. sistj = SistjClient()
  5. pje.login()   ← tenta storage state; se falhar, abre navegador visível
  6. sistj.login() ← tenta storage state; se falhar, abre navegador visível
  7. numeros = pje.coletar_lista_processos()
  8. para cada numero: processar_processo(...)
  9. pendentes = db.listar_aguardando_aprovacao()
  10. se pendentes: enviar_alerta(pendentes)
  11. emitir_pendentes()  ← NOVO: processa status='aprovado'
  12. finally: fechar browsers
```

**Alterações específicas:**
- `pje.login()` e `sistj.login()` agora são não-bloqueantes quando a sessão está viva, e bloqueantes-interativos quando expirou.
- Adicionar chamada a `emitir_pendentes()` antes do teardown — o agente também processa a fila de emissão.
- O cron continua útil para execuções automáticas, mas **apenas quando a sessão está viva**. Se a sessão expirou, a execução do cron abrirá um navegador visível (o que pode ser inesperado). Recomenda-se que o operador execute o agente manualmente pela primeira vez de cada dia para renovar a sessão, e o cron cuide das execuções subsequentes.

### 4.2 Como fica o `PjeClient.login()` e `SistjClient.login()`

A lógica comum de autenticação é extraída para a classe base `PlaywrightClient`. Cada cliente implementa apenas o que é específico:

```python
class PlaywrightClient:
    # ... atributos existentes ...
    
    def _autenticar_com_storage_state(
        self,
        url: str,
        storage_path: Path,
        indicadores_sucesso: List[str],
        login_manual_fn: Callable,
    ) -> bool:
        """
        1. Se storage_path existe, tenta carregar.
        2. Navega para url e verifica se sessão está viva.
        3. Se viva, retorna True.
        4. Se expirada, chama login_manual_fn() que abre navegador visível,
           espera operador logar, e retorna.
        5. Salva novo storage state.
        """
```

`PjeClient.login()` passa a ser um wrapper:
```python
def login(self) -> bool:
    return self._autenticar_com_storage_state(
        url=PJE_URL,
        storage_path=STORAGE_STATE_PJE,
        indicadores_sucesso=["Meu Perfil", "Sair", "Logout"],
        login_manual_fn=self._login_manual_pje,
    )
```

`SistjClient.login()` segue o mesmo padrão.

### 4.3 Como fica a emissão pós-aprovação (hoje quebrada)

**Hoje:**
- API recebe POST `/aprovar/{id}`
- API atualiza status para `aprovado`
- API dispara `BackgroundTasks` com `_disparar_emissao()`
- `_disparar_emissao` tenta importar `modulos.emissor` (não existe no container API) → falha silenciosamente
- Processo fica como `aprovado` para sempre, sem emissão

**Futuro:**
- API recebe POST `/aprovar/{id}`
- API atualiza status para `aprovado` (apenas isso)
- **Remove** `BackgroundTasks` e `_disparar_emissao` completamente
- O agente, em seu loop normal (ou via script `emitir_pendentes.py` chamado ao final do `main.py`), busca processos com `status='aprovado'` e executa:
  1. `sistj.login()` (reutiliza storage state)
  2. `sistj.gravar_e_aprovar(numero_sem_mascara)` → baixa PDF
  3. `pje.login()` (reutiliza storage state)
  4. `pje.anexar_demonstrativo(numero, caminho_pdf)`
  5. `db.atualizar_status(processo_id, 'emitido')`

Isso elimina a dependência da API ter Playwright, e usa o fato de que agente e API já compartilham o SQLite via filesystem.

### 4.4 Docker Compose continua relevante?

**Sim, parcialmente.**

| Componente | Antes | Depois |
|---|---|---|
| **agente** | Container Docker com cron | **Host nativo** (Python venv) para acesso ao display e storage state |
| **api** | Container Docker | Container Docker (inalterado) |
| **frontend** | Container Docker | Container Docker (inalterado) |
| **nginx** | Container Docker | Container Docker (inalterado) |
| **SQLite** | Volume `./dados` | Volume `./dados` (compartilhado entre host e containers) |

O `docker-compose.yml` perde o serviço `agente`. Um novo script `run_agente.sh` (ou `python -m agente.src.main`) é criado para execução no host.

Para desenvolvimento, o `docker-compose.dev.yml` pode manter o `agente` como opção, mas o dev precisa saber que autenticação interativa requer `--network host` ou similar para acessar o display.

---

## 5. Plano de Implementação Detalhado e Sequencial

---

### Fase 1 — Adaptação da Autenticação (Sessão Pré-Autenticada)

#### 5.1.1 Arquivos a criar / modificar / deletar

| Ação | Caminho | Motivo |
|---|---|---|
| **Criar** | `agente/src/modulos/auth_manager.py` | Gerenciador de storage state e fallback interativo |
| **Modificar** | `agente/src/modulos/playwright_client.py` | Integrar `auth_manager`, suportar `headless=False` no fallback |
| **Modificar** | `agente/src/modulos/pje.py` | Refatorar `login()` para usar `auth_manager` |
| **Modificar** | `agente/src/modulos/sistjweb.py` | Refatorar `login()` para usar `auth_manager` |
| **Modificar** | `agente/src/config.py` | Adicionar `STORAGE_STATE_DIR` e `STORAGE_STATE_PJE` / `STORAGE_STATE_SISTJ` |
| **Modificar** | `agente/src/main.py` | Chamar `emitir_pendentes()` antes do teardown |
| **Modificar** | `.env.agente` | Adicionar variáveis de storage state (opcional, com defaults) |
| **Deletar** | `agente/crontab` | O cron perde utilidade primária; substituir por script de execução manual ou scheduler interno |
| **Criar** | `run_agente.sh` | Script wrapper para execução no host (ativa venv, roda main.py) |
| **Modificar** | `docker-compose.yml` | Remover serviço `agente`; adicionar comentário explicativo |
| **Modificar** | `docker-compose.dev.yml` | Adicionar nota sobre limitações do agente em container para auth interativa |

#### 5.1.2 Interfaces e Contratos

**`agente/src/modulos/auth_manager.py`**

```python
from pathlib import Path
from typing import List, Callable, Optional
from playwright.sync_api import sync_playwright, Page, BrowserContext, TimeoutError as PlaywrightTimeout

class AuthManager:
    def __init__(self, storage_path: Path, headless_default: bool = True):
        self.storage_path = storage_path
        self.headless_default = headless_default
        self._playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def iniciar(self, accept_downloads: bool = False):
        """Inicializa Playwright com storage state se disponível."""
        ...

    def autenticar(
        self,
        url: str,
        verificar_sucesso_fn: Callable[[Page], bool],
        login_interativo_fn: Callable[[], Page],
    ) -> bool:
        """
        Fluxo:
        1. Se storage_path existe, carrega em new_context().
        2. Navega para url.
        3. Chama verificar_sucesso_fn(page).
        4. Se True → sessão válida, retorna True.
        5. Se False → chama login_interativo_fn() que retorna uma Page logada.
        6. Salva storage state da nova página/contexto.
        7. Retorna True.
        """
        ...

    def salvar_estado(self):
        """Persiste o estado atual do contexto em storage_path."""
        ...

    def fechar(self):
        """Fecha browser e playwright."""
        ...
```

**`agente/src/config.py` — adições:**

```python
# Storage State
STORAGE_STATE_DIR = Path(os.getenv("STORAGE_STATE_DIR", str(Path.home() / ".sog" / "auth")))
STORAGE_STATE_PJE = Path(os.getenv("STORAGE_STATE_PJE", str(STORAGE_STATE_DIR / "pje_storage.json")))
STORAGE_STATE_SISTJ = Path(os.getenv("STORAGE_STATE_SISTJ", str(STORAGE_STATE_DIR / "sistj_storage.json")))
```

**`agente/src/modulos/playwright_client.py` — modificações:**

```python
class PlaywrightClient:
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None  # NOVO
        self.page: Optional[Page] = None
        self._playwright = None
        self._auth_manager: Optional[AuthManager] = None  # NOVO

    def iniciar(self, accept_downloads: bool = False, storage_state: Optional[Path] = None):
        """Inicializa com storage state opcional."""
        self._playwright = sync_playwright().start()
        self.browser = self._playwright.chromium.launch(headless=HEADLESS)
        self.context = self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            accept_downloads=accept_downloads,
            storage_state=str(storage_state) if storage_state and storage_state.exists() else None,
        )
        self.page = self.context.new_page()
        self.page.set_default_timeout(TIMEOUT_PADRAO)

    def fechar(self):
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self._playwright:
            self._playwright.stop()
```

**`PjeClient.login()` — novo fluxo:**

```python
def login(self) -> bool:
    if not self.page:
        self.iniciar(accept_downloads=True, storage_state=STORAGE_STATE_PJE)
    
    # 1. Tenta navegar e verificar se já está logado
    self.page.goto(PJE_URL, wait_until="networkidle")
    self.page.wait_for_timeout(2000)
    
    if self._esta_logado():
        info("Login PJE via storage state válido.")
        return True
    
    # 2. Sessão expirada — fallback interativo
    aviso("Sessão PJE expirada. Abrindo navegador para login manual...")
    self.fechar()
    
    # Abre novo navegador visível
    self._playwright = sync_playwright().start()
    self.browser = self._playwright.chromium.launch(headless=False)  # VISÍVEL
    self.context = self.browser.new_context(viewport={"width": 1920, "height": 1080})
    self.page = self.context.new_page()
    
    self.page.goto(PJE_URL, wait_until="networkidle")
    input("[PJe] Faça login no navegador e pressione ENTER para continuar...")
    
    # 3. Verifica login
    if not self._esta_logado():
        erro("Login PJE não confirmado após interação manual.")
        return False
    
    # 4. Salva storage state
    STORAGE_STATE_DIR.mkdir(parents=True, exist_ok=True)
    self.context.storage_state(path=str(STORAGE_STATE_PJE))
    info(f"Storage state PJE salvo em {STORAGE_STATE_PJE}")
    return True

# Extrair verificação de login para método reutilizável
```

**Observação:** O mesmo padrão se aplica a `SistjClient.login()`.

#### 5.1.3 Dependências

Nenhuma nova dependência Python. Playwright já está instalado.

#### 5.1.4 Critérios de Aceite Mensuráveis

- [ ] `STORAGE_STATE_PJE` e `STORAGE_STATE_SISTJ` são criados automaticamente após primeiro login manual bem-sucedido.
- [ ] Execução subsequente do agente (com storage state válido) não abre navegador visível e não pede interação.
- [ ] Quando o storage state está ausente ou a sessão expirou, o agente abre um navegador visível (`headless=False`), exibe a URL de login, e pausa com `input()` até o operador pressionar ENTER.
- [ ] Após login manual, o arquivo JSON de storage state é atualizado com cookies e localStorage/sessionStorage.
- [ ] O `PlaywrightClient` fecha o contexto e browser sem vazamento de recursos (validar com `lsof` ou inspeção de processos).
- [ ] Teste manual: operador limpa `~/.sog/auth/`, executa agente, faz login nos dois sistemas, agente completa o pipeline. Segunda execução roda sem intervenção.

---

### Fase 2 — Correção CR-002 (Escaping CSS em pje.py)

#### 5.2.1 Contexto

O CR-002 identifica seletores CSS interpolados com texto dinâmico sem escaping, criando risco de injeção CSS (quebra de seletores ou, em cenários extremos, execução de código JS via seletores malformados).

Auditando o código atual (`agente/src/modulos/pje.py`):
- Linhas 147–153: `_clicar_por_texto_exato` usa `escape_for_css` ✅
- Linhas 213–216: `_aguardar_e_clicar_menu` usa `escape_for_css` ✅
- Linha 377: etiqueta usa `escape_for_css` ✅
- Linhas 420–422: número do processo usa `escape_for_css` ✅
- Linhas 555–557: número do processo usa `escape_for_css` ✅

**Porém**, o `selectors.py` contém templates com placeholders (`{etiqueta}`, `{numero}`, `{valor}`) que **não são usados atualmente** via `.format()`, mas representam risco se alguém passar a usá-los no futuro sem sanitização.

Além disso, `sistjweb.py:338` usa:
```python
seletores_radio = [s.format(valor=valor_radio) for s in RADIO_ITEM_CALCULO]
```
Onde `valor_radio = item["item_calculo"]` vem de `regras.py`. Como as regras são hardcoded e controladas, o risco é baixo, mas a prática é ruim.

#### 5.2.2 Arquivos a criar / modificar / deletar

| Ação | Caminho | Motivo |
|---|---|---|
| **Criar** | `agente/src/modulos/css_escape.py` | Extrair `escape_for_css` para módulo utilitário compartilhado |
| **Modificar** | `agente/src/modulos/pje.py` | Importar de `css_escape`; garantir que TODO texto dinâmico em seletor passa por escape |
| **Modificar** | `agente/src/modulos/sistjweb.py` | Importar de `css_escape`; substituir `.format()` por escape explícito |
| **Modificar** | `agente/src/modulos/selectors.py` | Documentar que templates são INSEGUROS e devem ser usados apenas com `escape_for_css`; ou refatorar para funções geradoras |

#### 5.2.3 Interfaces e Contratos

**`agente/src/modulos/css_escape.py`**

```python
import re

_RE_CSS_SPECIAL = re.compile(r'([\\"\'\x00-\x1f\x7f])')

def escape_for_css(texto: str) -> str:
    """
    Escapa caracteres perigosos para uso em seletores CSS.
    Cobre: aspas simples, aspas duplas, backslash, e caracteres de controle.
    """
    if not texto:
        return ""
    # Escapa backslash primeiro para não duplicar escapes
    texto = texto.replace("\\", "\\\\")
    texto = texto.replace("'", "\\'")
    texto = texto.replace('"', '\\"')
    return texto
```

**Refatoração em `sistjweb.py:338`:**

```python
from modulos.css_escape import escape_for_css

# Antes (inseguro se dados viessem de fonte externa):
# seletores_radio = [s.format(valor=valor_radio) for s in RADIO_ITEM_CALCULO]

# Depois (determinístico e seguro):
valor_escapado = escape_for_css(valor_radio)
seletores_radio = [
    f"input[value='{valor_escapado}'][name*='itemCalculo']",
    f"input[value='{valor_escapado}'][name*='item']",
    f"input[type='radio'][value='{valor_escapado}']",
]
```

**Refatoração em `selectors.py`:**

Remover templates com placeholders do arquivo de constantes. Se precisarem existir, transformar em funções:

```python
# Antes:
PJE_LINK_PROCESSO = [
    "a:has-text('{numero}')",
    ...
]

# Depois:
def pje_link_processo_seletores(numero: str) -> List[str]:
    from modulos.css_escape import escape_for_css
    n = escape_for_css(numero)
    return [
        f"a:has-text('{n}')",
        f"td:has-text('{n}')",
        f"span:has-text('{n}')",
        f"text='{n}'",
    ]
```

#### 5.2.4 Critérios de Aceite Mensuráveis

- [ ] Não existe nenhum `f"...{variavel}..."` ou `.format()` em seletores CSS onde `variavel` possa conter aspas, backslash ou caracteres de controle, sem passar por `escape_for_css`.
- [ ] `escape_for_css` possui testes unitários cobrindo: string vazia, aspas simples, aspas duplas, backslash, string comum, e string com múltiplos caracteres especiais.
- [ ] `selectors.py` não contém templates com placeholders `{...}` expostos como constantes globais.
- [ ] Scan estático (grep por `:has-text\(` + `f"` ou `.format`) retorna zero ocorrências não escapadas em `agente/src/modulos/`.

---

### Fase 3 — Integração de Custas Iniciais no Payload SISTJWEB

#### 5.3.1 Contexto

`extrator_pdf.extrair_texto_pdf()` retorna:
```json
{
  "custas_iniciais": {
    "encontrado": true,
    "valor_total": "266,95",
    "valor_total_centavos": 26695,
    "detalhamento": {"distribuidor": "100,00", "contador": "50,00", ...},
    "doc_id": "206426308",
    "numero_guia": "001-9",
    "vencimento": "11/08/2024",
    "scanned": false
  }
}
```

Hoje, `main.py` chama `processar_documentos(docs, textos)` em `agente/src/modulos/parser.py`. Precisamos verificar se `parser.py` propaga `custas_iniciais` para `dados_parser`.

O payload do SISTJWEB (`_construir_payload`) contém `"custas_pagas": [...]` (lista de dicts com `data`, `valor`, `numero_guia`). As custas iniciais extraídas do PDF devem ser convertidas para esse formato e adicionadas à lista `custas_pagas`.

#### 5.3.2 Arquivos a criar / modificar / deletar

| Ação | Caminho | Motivo |
|---|---|---|
| **Modificar** | `agente/src/modulos/parser.py` | Receber o resultado de `extrair_texto_pdf` e propagar `custas_iniciais` no dict de retorno |
| **Modificar** | `agente/src/main.py` | Passar os dados do PDF para o parser; ou extrair custas iniciais separadamente e incluir no payload |
| **Modificar** | `agente/src/main.py` `_construir_payload` | Converter `custas_iniciais` em entrada(s) na lista `custas_pagas` |

#### 5.3.3 Interfaces e Contratos

**Modificação em `main.py` — `_coletar_documentos`:**

Hoje:
```python
docs, textos = pje.coletar_documentos(numero)
dados_parser = processar_documentos(docs, textos)
```

O `pje.coletar_documentos` retorna `docs` (lista de metadados) e `textos` (dict doc_id → texto). Mas o extrator de custas iniciais precisa do **PDF** do processo, não apenas dos textos extraídos via Playwright.

**Análise:** O `coletar_documentos` no PJe lê o conteúdo dos documentos via iframe/modal (texto HTML). O `extrator_pdf` precisa de um arquivo PDF. No fluxo atual, o PDF do processo não é baixado — apenas os textos são lidos.

**Alternativas:**
1. Baixar o PDF da capa do processo no PJe e passar para `extrair_texto_pdf`.
2. Usar os textos já extraídos dos documentos "Comprovante de Pagamento de Custas" e tentar extrair valores por regex diretamente (sem PyMuPDF).

A alternativa 1 é mais robusta porque reutiliza o extrator já testado. Porém, adiciona uma etapa de download de PDF no PJe.

**Decisão:** Implementar a **Alternativa 1** — baixar o PDF da guia de custas quando o tipo for "Comprovante de Pagamento de Custas" ou "Guia", e extrair via `extrair_custas_iniciais`.

**Nova função em `pje.py`:**

```python
def baixar_documento_pdf(self, doc_id: str, caminho_destino: str) -> bool:
    """Baixa o PDF de um documento específico do processo."""
    ...
```

**Modificação em `main.py` `_coletar_documentos`:**

```python
docs, textos = pje.coletar_documentos(numero)

# Tenta baixar PDFs de guias de custas para extração de valores
custas_iniciais = {"encontrado": False, "scanned": False}
for doc in docs:
    if doc["tipo"].lower() in ("comprovante de pagamento de custas", "guia"):
        pdf_path = f"/tmp/{doc['doc_id']}.pdf"
        if pje.baixar_documento_pdf(doc["doc_id"], pdf_path):
            resultado_pdf = extrair_texto_pdf(pdf_path)
            if resultado_pdf["custas_iniciais"]["encontrado"]:
                custas_iniciais = resultado_pdf["custas_iniciais"]
                break

dados_parser = processar_documentos(docs, textos, custas_iniciais=custas_iniciais)
```

**Modificação em `_construir_payload`:**

```python
custas_pagas = dados_parser.get("custas_pagas", [])
custas_iniciais = dados_parser.get("custas_iniciais", {})
if custas_iniciais.get("encontrado"):
    custas_pagas.append({
        "data": custas_iniciais.get("vencimento", ""),
        "valor": custas_iniciais.get("valor_total", ""),
        "numero_guia": custas_iniciais.get("numero_guia", ""),
    })

payload = {
    ...
    "custas_pagas": custas_pagas,
    ...
}
```

#### 5.3.4 Dependências

Nenhuma — reutiliza `pymupdf` já instalado.

#### 5.3.5 Critérios de Aceite Mensuráveis

- [ ] Quando um processo possui documento do tipo "Comprovante de Pagamento de Custas" ou "Guia", o agente baixa o PDF e extrai os valores.
- [ ] O campo `custas_pagas` no payload do SISTJWEB contém, no mínimo, uma entrada com `data`, `valor` e `numero_guia` provenientes das custas iniciais.
- [ ] Se o PDF for scanned (`scanned=True`), o agente registra log de aviso e não tenta preencher custas iniciais (evita dados incorretos).
- [ ] Se não houver guia de custas no processo, o payload continua funcionando normalmente (`custas_pagas` vazia ou com dados do parser).
- [ ] Teste com pelo menos 3 processos reais: um com guia de custas, um sem guia, e um com PDF scanned.

---

### Fase 4 — Fila de Emissão Pós-Aprovação

#### 5.4.1 Contexto

Hoje a API tenta emitir em background, mas falha porque não tem Playwright. A solução é mover a emissão para o agente, que já tem Playwright e já compartilha o SQLite.

#### 5.4.2 Arquivos a criar / modificar / deletar

| Ação | Caminho | Motivo |
|---|---|---|
| **Modificar** | `api/src/rotas/aprovacao.py` | Remover `BackgroundTasks` e `_disparar_emissao`; apenas atualizar status para `aprovado` |
| **Criar** | `agente/src/emitir_pendentes.py` | Script/entry point para processar fila de emissão |
| **Modificar** | `agente/src/main.py` | Chamar `emitir_pendentes()` ao final do pipeline |
| **Modificar** | `agente/src/modulos/emissor.py` | Garantir que reutiliza storage state (não faz login programático) |
| **Criar** | `shared/sog_shared/db.py` — `listar_aprovados()` | Query para buscar processos com status `aprovado` |

#### 5.4.3 Interfaces e Contratos

**`shared/sog_shared/db.py` — nova função:**

```python
def listar_aprovados(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM processos WHERE status = 'aprovado' ORDER BY atualizado_em LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]
```

**`agente/src/emitir_pendentes.py`:**

```python
"""Processa a fila de emissão: processos aprovados → emitidos."""
from modulos.sistjweb import SistjClient
from modulos.pje import PjeClient
from sog_shared import db
from utils.logger import info, erro


def emitir_pendentes():
    pendentes = db.listar_aprovados()
    if not pendentes:
        info("Nenhum processo aprovado pendente de emissão.")
        return

    sistj = SistjClient()
    pje = PjeClient()

    try:
        # Pré-autentica nos dois sistemas (reutiliza storage state)
        if not sistj.login():
            raise RuntimeError("Falha no login SISTJWEB para emissão")
        if not pje.login():
            raise RuntimeError("Falha no login PJe para emissão")

        for proc in pendentes:
            processo_id = proc["id"]
            numero = proc["numero"]
            numero_sem_mascara = proc["numero_sem_mascara"]
            try:
                caminho_pdf = sistj.gravar_e_aprovar(numero_sem_mascara)
                pje.anexar_demonstrativo(numero, caminho_pdf)
                db.atualizar_status(processo_id, "emitido")
                db.registrar_log(processo_id, "emissao", "ok", f"Demonstrativo: {caminho_pdf}")
                info(f"Processo {numero} emitido e anexado.")
            except Exception as exc:
                db.atualizar_status(processo_id, "erro", str(exc))
                db.registrar_log(processo_id, "emissao", "erro", str(exc))
                erro(f"Falha na emissão de {numero}: {exc}")
    finally:
        sistj.fechar()
        pje.fechar()


if __name__ == "__main__":
    emitir_pendentes()
```

**`api/src/rotas/aprovacao.py` — simplificado:**

```python
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

    return {"message": "Aprovação registrada. O agente processará a emissão."}
```

#### 5.4.4 Dependências

Nenhuma.

#### 5.4.5 Critérios de Aceite Mensuráveis

- [ ] Após aprovação via dashboard, o processo muda para status `aprovado` e a API responde imediatamente (sem background task).
- [ ] O container `api` não contém código nem import relacionado a Playwright ou emissão.
- [ ] Quando o agente executa (manualmente ou via cron), processos `aprovado` são automaticamente emitidos no SISTJWEB e anexados no PJe.
- [ ] Após emissão bem-sucedida, status muda para `emitido`.
- [ ] Se a emissão falhar, status muda para `erro` e `tentativas` é incrementada (para permitir retry).
- [ ] O operador pode executar `python agente/src/emitir_pendentes.py` isoladamente para processar apenas a fila de emissão, sem rodar o pipeline completo.
- [ ] Teste de integração: aprovar processo via API → executar agente → verificar que processo aparece como `emitido` no histórico.

---

### Fase 5 — Mapeamento das Regras de Custas para Criminal, Família, Fazenda Pública

#### 5.5.1 Contexto

Hoje `regras.py` possui:
```python
REGRAS_OUTROS_ITENS = {
    "civel_comum": [...],
    "familia": [],
    "fazenda_publica": [],
    "criminal": [],
    "default": [],
}
```

Quando a área é `familia`, `fazenda_publica`, `criminal` ou `default`, o pipeline define status como `pendente_manual` e notifica o operador. Isso é um gargalo operacional.

#### 5.5.2 O que precisa ser mapeado

Cada área do direito no TJDFT possui uma combinação específica de itens da guia de custas no SISTJWEB. Exemplos típicos (a confirmar com a contadora):

- **Família**: pode incluir distribuidor, contador, ofícios (comunicação de cartório), etc.
- **Fazenda Pública**: pode ter isenção de custas parcial, não cobrança de distribuidor em certos casos, etc.
- **Criminal**: geralmente isento de custas (art. 789 CPP), mas pode haver custas em ação civil ex delito ou em procedimentos específicos.

**⚠️ O mapeamento exato requer conhecimento jurídico-operacional.** O desenvolvedor não deve inventar regras. Deve coletar da contadora/operadora.

#### 5.5.3 Arquivos a criar / modificar / deletar

| Ação | Caminho | Motivo |
|---|---|---|
| **Modificar** | `agente/src/regras.py` | Preencher `familia`, `fazenda_publica`, `criminal` com regras validadas |
| **Criar** | `docs/regras_custas_tjdft.md` | Documentação das regras por área, com fonte (ex: Resolução do TJDFT, manual SISTJWEB) |

#### 5.5.4 Interfaces e Contratos

**Formato de cada regra (já existente):**

```python
{
    "item_guia": str,           # ex: "Distribuidor", "Custas", "Ofícios"
    "item_calculo": str,        # ex: "D-I-a", "G-I"
    "quantidade": int,          # ex: 1
    "usa_ids_oficios": bool,    # opcional
    "usa_valor_causa_atualizado": bool,  # opcional
}
```

**Processo de coleta (a ser executado pelo dev + operador):**

1. O operador acessa o SISTJWEB manualmente para cada área.
2. Anota quais itens aparecem no dropdown "Item da Guia" e quais radios de cálculo são selecionados para processos típicos.
3. Documenta em `docs/regras_custas_tjdft.md`.
4. O dev traduz para o formato Python em `regras.py`.
5. Testa com processos reais de cada área.

#### 5.5.5 Dependências

Nenhuma.

#### 5.5.6 Critérios de Aceite Mensuráveis

- [ ] `regras.py` contém pelo menos uma regra não-vazia para `familia`.
- [ ] `regras.py` contém pelo menos uma regra não-vazia para `fazenda_publica`.
- [ ] `regras.py` contém pelo menos uma regra não-vazia para `criminal`.
- [ ] `docs/regras_custas_tjdft.md` documenta a fonte de cada regra (ex: "Baseado em Resolução TJDFT nº X/YYYY, item Z").
- [ ] Teste com pelo menos 1 processo real de cada área: o pipeline preenche a planilha SISTJWEB sem cair em `pendente_manual`.
- [ ] Se uma área não tiver regra mapeada, o sistema continua caindo graciosamente em `pendente_manual` (comportamento existente preservado).

---

## 6. Riscos e Pontos de Atenção

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| **Sessão do SSO Microsoft expira em < 1h** | Média | Alto | Implementar detecção de expiração no início de cada execução. Se expirada, abortar e notificar operador para reautenticar. Considerar reduzir frequência do cron (ex: a cada 4h em vez de 1h). |
| **Playwright detectado como bot pelo PJe/SISTJWEB** | Baixa | Alto | Usar `headless=False` no fallback interativo garante interação humana real no login. Manter `user-agent` padrão do Chromium (não sobrescrever). Evitar ações rápidas demais (já há `wait_for_timeout` espalhado). |
| **SQLite race condition entre agente (host) e API (container)** | Baixa | Alto | O SQLite já está em WAL mode (`PRAGMA journal_mode=WAL`) e ambos usam `BEGIN IMMEDIATE`. Manter timeouts altos (`busy_timeout=5000`). Se PostgreSQL for priorizado, essa race condition desaparece. |
| **Operador esquece de autenticar e o cron roda sem sessão** | Média | Médio | No modo sem sessão, o agente abre navegador visível e pausa. Se executado via cron em background, o `input()` vai travar indefinidamente. **Mitigação:** remover o cron ou adaptá-lo para detectar se está rodando em TTY interativo. Se não estiver, logar erro e sair sem travar. |
| **Mapeamento de regras judiciais incorreto** | Média | Alto | Nunca inventar regras. Sempre validar com a contadora/operadora usando processos reais. Manter fallback para `pendente_manual`. |
| **Agente no host depende de bibliotecas do sistema (Chromium)** | Média | Médio | Documentar requisitos do sistema operacional. Criar script `setup_host.sh` que instala Python 3.12, venv, dependências Python, e browsers Playwright. |
| **Rollback do deploy para VPS futuramente** | Baixa | Médio | Manter o código do agente containerizável. A única dependência de host é o display (para fallback interativo). Em VPS, o fallback interativo não funciona — mas se o SSO mudar para permitir login programático no futuro, o código pode voltar a ser containerizado facilmente. |

---

## 7. Decisões de Baixa Reversibilidade

1. **Agente fora do Docker** (Seção 3)
   - Justificativa: Navegador visível e storage state no filesystem do host.
   - Rollback: Restaurar serviço `agente` no `docker-compose.yml` e mover execução para container.

2. **Remoção de `BackgroundTasks` de emissão da API** (Fase 4)
   - Justificativa: A API nunca teve Playwright; a emissão em background era código-morto que falhava silenciosamente.
   - Rollback: Reverter `aprovacao.py` para versão anterior (mantida no git).

3. **Remoção do cron como mecanismo primário** (Fase 1)
   - Justificativa: Com autenticação manual, o cron é impraticável quando a sessão expira.
   - Rollback: Restaurar `agente/crontab` e configurar execução via cron novamente (se o ambiente de autenticação mudar no futuro).

---

## 8. Checklist de Execução para o Desenvolvedor

- [ ] Fase 1: `auth_manager.py` criado e testado com login manual + reutilização.
- [ ] Fase 1: `PjeClient` e `SistjClient` refatorados para usar `auth_manager`.
- [ ] Fase 1: Script `run_agente.sh` criado e documentado.
- [ ] Fase 1: `docker-compose.yml` atualizado (sem serviço `agente`).
- [ ] Fase 2: `css_escape.py` criado com testes unitários.
- [ ] Fase 2: Zero seletores interpolados sem escaping em `agente/src/modulos/`.
- [ ] Fase 3: `pje.py` possui método `baixar_documento_pdf`.
- [ ] Fase 3: `main.py` integra custas iniciais no payload.
- [ ] Fase 3: Teste com 3 processos reais (com guia, sem guia, scanned).
- [ ] Fase 4: API `/aprovar` não usa `BackgroundTasks`.
- [ ] Fase 4: `emitir_pendentes.py` processa fila corretamente.
- [ ] Fase 4: Teste de integração: aprovar → agente emitir → status `emitido`.
- [ ] Fase 5: Regras coletadas da contadora para Criminal, Família, Fazenda Pública.
- [ ] Fase 5: `regras.py` populado e testado com processos reais de cada área.
- [ ] Fase 5: `docs/regras_custas_tjdft.md` documentado.
- [ ] MEMORY.md atualizado com decisões arquiteturais deste plano.
