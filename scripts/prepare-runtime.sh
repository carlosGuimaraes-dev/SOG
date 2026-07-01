#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_TEMPLATE="$ROOT_DIR/.env.example"
API_ENV="$ROOT_DIR/.env.api"
AGENTE_ENV="$ROOT_DIR/.env.agente"
DADOS_DIR="$ROOT_DIR/dados"
AUTH_DIR="$DADOS_DIR/auth"
PREP_SCRIPT="$ROOT_DIR/scripts/prepare-internal-runtime.py"

if [[ ! -f "$ENV_TEMPLATE" ]]; then
  echo "Template ausente: $ENV_TEMPLATE" >&2
  exit 1
fi

mkdir -p "$DADOS_DIR/screenshots" "$DADOS_DIR/demonstrativos" "$AUTH_DIR"

copy_if_missing() {
  local src="$1"
  local dest="$2"

  if [[ -f "$dest" ]]; then
    echo "Mantido: $(basename "$dest")"
    return
  fi

  cp "$src" "$dest"
  echo "Criado: $(basename "$dest") a partir de $(basename "$src")"
}

copy_if_missing "$ENV_TEMPLATE" "$API_ENV"
copy_if_missing "$ENV_TEMPLATE" "$AGENTE_ENV"

if [[ -f "$PREP_SCRIPT" ]]; then
  python3 "$PREP_SCRIPT" --non-interactive
fi

cat <<EOF

Runtime interno preparado.

Arquivos de ambiente:
- $API_ENV
- $AGENTE_ENV

Diretórios persistentes:
- $DADOS_DIR
- $AUTH_DIR

Próximos passos:
1. Preencha os segredos reais em .env.api e .env.agente.
2. Revise JWT_SECRET_KEY e DASHBOARD_SENHA_HASH em .env.api.
3. Revise DATAJUD_API_KEY, TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID em .env.agente.
4. Se o preparo estiver pronto, suba o ambiente com: ./scripts/start-local.sh
EOF
