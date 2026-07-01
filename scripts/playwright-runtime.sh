#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-/paperclip/.cache/ms-playwright}"
CHROMIUM_DIR="${PLAYWRIGHT_CHROMIUM_DIR:-}"
CHROMIUM_BIN="${PLAYWRIGHT_CHROMIUM_BIN:-}"
HEADLESS="${HEADLESS:-}"
URL="${1:-about:blank}"

REQUIRED_LIBS=(
  "libglib-2.0.so.0"
  "libgobject-2.0.so.0"
  "libgio-2.0.so.0"
  "libnspr4.so"
  "libnss3.so"
  "libnssutil3.so"
  "libsmime3.so"
  "libatk-1.0.so.0"
  "libatk-bridge-2.0.so.0"
  "libdbus-1.so.3"
  "libcups.so.2"
  "libxcb.so.1"
  "libxkbcommon.so.0"
  "libasound.so.2"
  "libgbm.so.1"
  "libX11.so.6"
  "libXext.so.6"
  "libcairo.so.2"
  "libpango-1.0.so.0"
  "libXcomposite.so.1"
  "libXdamage.so.1"
  "libXfixes.so.3"
  "libXrandr.so.2"
  "libatspi.so.0"
)

find_chromium_bin() {
  if [[ -n "${CHROMIUM_BIN}" ]]; then
    printf '%s\n' "${CHROMIUM_BIN}"
    return 0
  fi

  if [[ -n "${CHROMIUM_DIR}" && -x "${CHROMIUM_DIR}/chrome-linux64/chrome" ]]; then
    printf '%s\n' "${CHROMIUM_DIR}/chrome-linux64/chrome"
    return 0
  fi

  if [[ -n "${CHROMIUM_DIR}" && -x "${CHROMIUM_DIR}/chrome-headless-shell-linux64/chrome-headless-shell" ]]; then
    printf '%s\n' "${CHROMIUM_DIR}/chrome-headless-shell-linux64/chrome-headless-shell"
    return 0
  fi

  local newest_dir
  newest_dir="$(find "${PLAYWRIGHT_BROWSERS_PATH}" -maxdepth 1 -type d -name 'chromium-*' | sort -V | tail -n 1 || true)"
  if [[ -n "${newest_dir}" && -x "${newest_dir}/chrome-linux64/chrome" ]]; then
    printf '%s\n' "${newest_dir}/chrome-linux64/chrome"
    return 0
  fi

  newest_dir="$(find "${PLAYWRIGHT_BROWSERS_PATH}" -maxdepth 1 -type d -name 'chromium_headless_shell-*' | sort -V | tail -n 1 || true)"
  if [[ -n "${newest_dir}" && -x "${newest_dir}/chrome-headless-shell-linux64/chrome-headless-shell" ]]; then
    printf '%s\n' "${newest_dir}/chrome-headless-shell-linux64/chrome-headless-shell"
    return 0
  fi

  return 1
}

print_required_packages() {
  cat <<'EOF'
Expected Debian/Ubuntu packages for Chromium in this runtime:
  libglib2.0-0
  libnss3
  libnspr4
  libatk1.0-0
  libatk-bridge2.0-0
  libdbus-1-3
  libcups2
  libx11-6
  libx11-xcb1
  libxcb1
  libxcomposite1
  libxdamage1
  libxext6
  libxfixes3
  libxrandr2
  libxkbcommon0
  libgbm1
  libasound2
  libcairo2
  libpango-1.0-0
  libatspi2.0-0
EOF
}

check_missing_libs() {
  local chrome_bin="$1"
  local ldd_output

  ldd_output="$(ldd "${chrome_bin}" 2>/dev/null || true)"
  if [[ -z "${ldd_output}" ]]; then
    echo "Unable to inspect Chromium with ldd: ${chrome_bin}" >&2
    return 2
  fi

  local missing=()
  for lib in "${REQUIRED_LIBS[@]}"; do
    if grep -Fq "${lib} => not found" <<<"${ldd_output}"; then
      missing+=("${lib}")
    fi
  done

  if [[ "${#missing[@]}" -gt 0 ]]; then
    echo "Playwright Chromium cannot start in this runtime." >&2
    echo "Missing shared libraries:" >&2
    printf '  - %s\n' "${missing[@]}" >&2
    echo >&2
    print_required_packages >&2
    return 1
  fi

  return 0
}

launch_chromium() {
  local chrome_bin="$1"
  local -a chrome_args=(
    "--no-sandbox"
    "--disable-dev-shm-usage"
    "--disable-gpu"
    "--disable-software-rasterizer"
    "--user-data-dir=${ROOT_DIR}/.cache/playwright-chromium-profile"
  )

  mkdir -p "${ROOT_DIR}/.cache/playwright-chromium-profile"

  if [[ -z "${HEADLESS}" ]]; then
    if [[ -n "${DISPLAY:-}" ]]; then
      HEADLESS="false"
    else
      HEADLESS="true"
    fi
  fi

  if [[ "${HEADLESS}" == "true" ]]; then
    chrome_args+=(
      "--headless=new"
      "--dump-dom"
    )
  fi

  exec "${chrome_bin}" "${chrome_args[@]}" "${URL}"
}

main() {
  local chrome_bin
  chrome_bin="$(find_chromium_bin)" || {
    echo "No Playwright Chromium binary found under ${PLAYWRIGHT_BROWSERS_PATH}." >&2
    echo "Set PLAYWRIGHT_CHROMIUM_BIN or PLAYWRIGHT_CHROMIUM_DIR if the browser is cached elsewhere." >&2
    exit 1
  }

  check_missing_libs "${chrome_bin}"
  launch_chromium "${chrome_bin}"
}

main "$@"
