#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PREP_RUNTIME_SCRIPT="$ROOT_DIR/scripts/prepare-runtime.sh"
DIAG_SCRIPT="$ROOT_DIR/scripts/runtime_diagnostics.py"

bash "$PREP_RUNTIME_SCRIPT"
python3 "$DIAG_SCRIPT" --preflight --write-report
docker compose -f "$ROOT_DIR/docker-compose.yml" up -d --build || {
  python3 "$DIAG_SCRIPT" --write-report || true
  exit 1
}
python3 "$DIAG_SCRIPT" --write-report
