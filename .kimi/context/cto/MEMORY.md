# MEMORY — CTO

> Arquivo dinâmico. Consulte antes de qualquer planejamento para manter
> consistência arquitetural entre sessões.

---

## Stack atual do projeto

- **Linguagem:** Python 3.12 (agente + API), TypeScript/React 18 (frontend)
- **Framework:** FastAPI 0.111 (API), React Router v6 (frontend)
- **Banco:** SQLite (migração para PostgreSQL 15 planejada — Wave 8)
- **Autenticação:** JWT via `python-jose` + `passlib` (migração para httpOnly cookies — Wave 3)
- **Testes:** pytest (agente), TestClient (API), Vitest + RTL + MSW (frontend — Wave 5)
- **Infra:** Docker Compose + Nginx (multi-stage build frontend)

---

## Decisões arquiteturais

<!-- Nunca delete — apenas adicione. -->

- **2026-05-15 | Auth: JWT em localStorage → httpOnly cookies**
  Decidido: Migrar tokens de `localStorage` para `httpOnly Secure SameSite=Strict` cookies emitidos pelo backend.
  Alternativas: Manter localStorage + CSP strita; usar sessionStorage.
  Motivo: Eliminar vetor XSS completo contra tokens de sessão (OWASP A01:2021).
  Reversibilidade: média — requer sincronia frontend+backend para rollback.

- **2026-05-15 | Banco: SQLite → PostgreSQL**
  Decidido: SQLite em WAL mode como ponte (Wave 4); PostgreSQL 15 como destino final (Wave 8).
  Alternativas: Manter SQLite com WAL eternamente; usar PostgreSQL imediato.
  Motivo: Resolver race conditions (CR-004), permitir concorrência real entre agente e API, e atender requisitos de backup/HA.
  Reversibilidade: **baixa** — migração de dados é unidirecional sem rollback trivial.

- **2026-05-15 | Pacote compartilhado `shared/`**
  Decidido: Extrair `db.py`, schemas Pydantic e config para pacote Python próprio (`shared/sog_shared/`).
  Alternativas: Manter `sys.path.insert` + cópia de código; usar submodules git.
  Motivo: Eliminar acoplamento crítico Agente→API (CR-008), permitir versionamento independente.
  Reversibilidade: alta — rollback via restauração de PYTHONPATH e cópia de arquivos.

- **2026-05-15 | Rate limiting: slowapi (memória)**
  Decidido: Usar `slowapi` com limitador em memória para MVP.
  Alternativas: Redis + fastapi-limiter; nginx limit_req sozinho.
  Motivo: Evitar dependência infra extra (Redis) antes do PostgreSQL; nginx limit_req complementa como camada externa.
  Reversibilidade: alta — substituir por Redis futuramente sem mudar contratos.

- **2026-05-15 | UX Dashboard: Filtros client-side no histórico**
  Decidido: Implementar filtros de histórico client-side inicialmente (status, data, valor).
  Alternativas: Filtros server-side via query params no `/historico`.
  Motivo: Endpoint não suporta filtros hoje; client-side é trivial e totalmente reversível. Migração para server-side não quebra UI.
  Reversibilidade: alta — só requer mover lógica de filtro para query string.

- **2026-05-15 | UX Dashboard: Threshold de valor alto hardcoded**
  Decidido: Threshold de "valor muito alto" = R$ 50.000,00 hardcoded no frontend.
  Alternativas: Campo configurável no banco (`config` table); variável de ambiente.
  Motivo: Não existe mecanismo de configuração no banco atual; valor pode ser extraído para config futura sem quebrar contrato.
  Reversibilidade: alta — alterar constante em `lib/formatters.ts` ou migrar para config dinâmica.

- **2026-05-15 | UX Dashboard: Status de emissão usa `erro` (não `erro_emissao`)**
  Decidido: O frontend trata status `erro` como falha na emissão.
  Alternativas: Alterar emissor.py para usar `erro_emissao`; criar estado intermediário.
  Motivo: Schema do banco e emissor usam `erro`. O TODO_frontend.md menciona `erro_emissao` incorretamente.
  Reversibilidade: alta — se `erro_emissao` for introduzido no futuro, basta adicionar ao enum de status.

- **2026-05-16 | Script utilitário de extração de sentença de PDF**
  Decidido: `pymupdf` (fitz) para extração de texto com análise de layout; script em `tools/testar_pdf.py` na raiz; heurística regex para isolar DISPOSITIVO (`ANTE O EXPOSTO`/`DISPOSITIVO`/`DECIDO`); detecção de PDF scanned via `get_text()` + presença de imagens.
  Alternativas: `pdfplumber` (MIT) — mais lenta, sem vantagem de layout para este caso; colocar script dentro de `agente/tools/` — reforça acoplamento com runtime.
  Motivo: PyMuPDF oferece extração por blocos (melhor para localizar dispositivo) e detecção nativa de scanned; script em raiz indica claramente que é ferramenta de dev/teste.
  Reversibilidade: alta para localização e heurística; **média** para biblioteca (AGPL-3.0) — trocar por `pdfplumber` requer apenas refatorar a função de extração de texto, pois o script isola a lib.

---

## Padrões do projeto

- Imports absolutos a partir de `src/` no frontend; imports de pacote `sog_shared` no Python.
- Variáveis de ambiente via `python-dotenv` no agente; lifespan do FastAPI para validação no startup da API.
- Logs estruturados em JSON (`agente/src/utils/logger.py` — positive finding).
- Queries SQLite parametrizadas com `?` placeholders (positive finding).
- Tokens JWT com claims `iss`, `aud`, `iat`, `exp`, `sub`, `type` (a partir de Wave 3).
- Parser de valor monetário deve ser extraído para `frontend/src/lib/formatters.ts` para reuso entre W2-F9 e W3-F13.

---

## Débitos técnicos identificados

- `api/src/auth.py:19`: JWT secret derivado de hash bcrypt com fallback hardcoded — **bloqueia deploy** (CR-003).
- `docker-compose.yml:59`: Volume de screenshots exposto no nginx sem autenticação — **bloqueia deploy** (CR-005).
- `agente/src/banco/db.py:174`: `_init_db()` executa no import global — causa side-effects e dificulta testes (M-012).
- `api/src/rotas/aprovacao.py:50`: Race condition entre SELECT e UPDATE em conexões diferentes — **bloqueia deploy** (CR-004).
- `frontend/src/lib/api.ts:8`: Tokens em `localStorage` — vetor XSS (CR-006).
- `api/src/rotas/auth.py:39-55`: Refresh token reutilizável infinitamente — **bloqueia deploy** (CR-014).
- `agente/src/modulos/pje.py:120-128`: Seletores CSS interpolados sem escaping — **bloqueia deploy** (CR-002).
- **Novo (2026-05-15)**: Endpoint `/historico` não suporta filtros server-side — pode virar gargalo se histórico > 500 registros (mitigação: filtros client-side por enquanto).
- **Novo (2026-05-15)**: Endpoint `/historico/exportar` (CSV) não existe — precisa ser criado na Wave 3 (W3-F14).

---

## Planos executados (índice)

- `.kimi/context/cto/code-review-fixes.md` — Plano técnico para 98 issues do code review enterprise (2026-05-15)
- `.kimi/context/cto/todo-frontend.md` — Plano técnico para 14 features de UX do dashboard, decomposto em 3 waves (2026-05-15)
- `.kimi/plans/extrator-pdf.md` — Plano técnico para script utilitário de extração de sentença de PDF (2026-05-16)
