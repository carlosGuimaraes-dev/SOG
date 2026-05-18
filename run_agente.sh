#!/bin/bash
# Wrapper de execução do agente de custas TJDFT no host nativo.
# Ativa venv, configura PYTHONPATH e inicia o serviço longo.

set -e

# Diretório base do projeto (onde este script reside)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Ativa venv se existir
if [ -f "$SCRIPT_DIR/agente/.venv/bin/activate" ]; then
    source "$SCRIPT_DIR/agente/.venv/bin/activate"
elif [ -f "$SCRIPT_DIR/.venv/bin/activate" ]; then
    source "$SCRIPT_DIR/.venv/bin/activate"
fi

# PYTHONPATH para shared/ e agente/src/
export PYTHONPATH="${SCRIPT_DIR}/shared:${SCRIPT_DIR}/agente/src:${PYTHONPATH}"

# Inicia o serviço longo
exec python "${SCRIPT_DIR}/agente/src/servico.py" "$@"
