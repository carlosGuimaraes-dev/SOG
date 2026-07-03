#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

changed_files="${CHANGED_FILES:-}"
base_ref="${BASE_REF:-}"

if [[ -z "$base_ref" ]]; then
  if git rev-parse --verify github/main >/dev/null 2>&1; then
    base_ref="github/main"
  else
    base_ref="origin/main"
  fi
fi

if [[ -z "$changed_files" ]]; then
  changed_files="$(git diff --name-only "${base_ref}...HEAD")"
fi

has_changed_file() {
  local needle="$1"
  grep -Fxq "$needle" <<<"$changed_files"
}

python_targets=()
node_targets=()

if has_changed_file "api/requirements.txt"; then
  python_targets+=("api/requirements.txt")
fi

if has_changed_file "agente/requirements.txt"; then
  python_targets+=("agente/requirements.txt")
fi

if has_changed_file "shared/pyproject.toml"; then
  python_targets+=("shared/pyproject.toml")
fi

if has_changed_file "frontend/package-lock.json" || has_changed_file "frontend/package.json"; then
  node_targets+=("frontend")
fi

if has_changed_file "desktop/package-lock.json" || has_changed_file "desktop/package.json"; then
  node_targets+=("desktop")
fi

if [[ ${#python_targets[@]} -eq 0 && ${#node_targets[@]} -eq 0 ]]; then
  echo "No dependency manifests changed in this diff; skipping repo-native dependency audit."
  exit 0
fi

echo "Dependency manifests selected for audit:"
printf '  - %s\n' "${python_targets[@]}" "${node_targets[@]}"

run_python_requirement_audit() {
  local requirement_file="$1"

  if ! command -v pip-audit >/dev/null 2>&1; then
    echo "pip-audit is required to scan ${requirement_file}" >&2
    exit 1
  fi

  pip-audit -r "$requirement_file"
}

run_python_pyproject_audit() {
  local pyproject_file="$1"
  local tmp_requirements

  tmp_requirements="$(mktemp)"
  python3 - "$pyproject_file" "$tmp_requirements" <<'PY'
import pathlib
import sys
import tomllib

pyproject_path = pathlib.Path(sys.argv[1])
requirements_path = pathlib.Path(sys.argv[2])
data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
dependencies = data.get("project", {}).get("dependencies", [])
requirements_path.write_text("\n".join(dependencies) + "\n", encoding="utf-8")
PY

  if [[ ! -s "$tmp_requirements" ]]; then
    echo "No installable dependencies found in ${pyproject_file}; skipping."
    rm -f "$tmp_requirements"
    return 0
  fi

  if ! command -v pip-audit >/dev/null 2>&1; then
    echo "pip-audit is required to scan ${pyproject_file}" >&2
    rm -f "$tmp_requirements"
    exit 1
  fi

  pip-audit -r "$tmp_requirements"
  rm -f "$tmp_requirements"
}

for target in "${python_targets[@]}"; do
  case "$target" in
    *.txt) run_python_requirement_audit "$target" ;;
    *.toml) run_python_pyproject_audit "$target" ;;
    *)
      echo "Unsupported Python dependency manifest: $target" >&2
      exit 1
      ;;
  esac
done

for target in "${node_targets[@]}"; do
  npm audit --omit=dev --package-lock-only --audit-level=high --prefix "$target"
done
