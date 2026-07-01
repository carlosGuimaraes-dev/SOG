#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEFAULT_PDF="$ROOT_DIR/image/Primeiro posso é abris PJe e.pdf"
INPUT_PDF="${1:-${SOG_QA_PDF_HOST_PATH:-}}"

if [[ -z "${INPUT_PDF}" ]]; then
  if [[ -f "${DEFAULT_PDF}" ]]; then
    INPUT_PDF="${DEFAULT_PDF}"
  else
    echo "Informe um PDF judicial real: ./scripts/qa-extrator-pdf.sh /caminho/processo.pdf" >&2
    echo "Ou defina SOG_QA_PDF_HOST_PATH e SOG_EXTRATOR_PDF_REAL." >&2
    exit 1
  fi
fi

if [[ ! -f "${INPUT_PDF}" ]]; then
  echo "PDF inexistente: ${INPUT_PDF}" >&2
  exit 1
fi

export SOG_QA_PDF_DIR="$(dirname "${INPUT_PDF}")"
export SOG_EXTRATOR_PDF_REAL="/fixtures/$(basename "${INPUT_PDF}")"

exec docker compose -f "${ROOT_DIR}/docker-compose.qa.yml" run --rm agente-qa-extrator-pdf
