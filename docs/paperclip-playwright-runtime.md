# Playwright Runtime in Paperclip

This repository now includes `scripts/playwright-runtime.sh` to diagnose and
launch the cached Playwright Chromium binary from the Paperclip runtime.

## Why this exists

The Paperclip execution container exposes a Playwright browser cache at
`/paperclip/.cache/ms-playwright`. Current headless validation relies on the
cached `chromium_headless_shell-*` artifact used by `npx playwright`.

Chromium will not start unless the base runtime also provides the Linux shared
libraries it depends on.

Without those libraries, the raw browser launch fails immediately with errors
like:

```text
error while loading shared libraries: libglib-2.0.so.0: cannot open shared object file
```

## Usage

```bash
./scripts/playwright-runtime.sh
./scripts/playwright-runtime.sh https://example.com
HEADLESS=false DISPLAY=:99 ./scripts/playwright-runtime.sh https://example.com
```

Behavior:

- finds the newest cached `chromium-*` or `chromium_headless_shell-*` browser
  under `PLAYWRIGHT_BROWSERS_PATH` or a path passed via
  `PLAYWRIGHT_CHROMIUM_BIN` / `PLAYWRIGHT_CHROMIUM_DIR`
- runs `ldd` and fails fast with the exact missing shared libraries
- launches Chromium with `--no-sandbox` and `--disable-dev-shm-usage`
- defaults to headless mode when `DISPLAY` is not set

## Current runtime result

As of 2026-05-31, the Paperclip runtime has the required shared libraries and a
working headless-shell cache. Verified smoke commands:

```bash
npx playwright --version
npx playwright screenshot --browser=chromium 'data:text/html,<title>SOGA-34 smoke</title><h1>ok</h1>' /tmp/soga34-smoke.png
./scripts/playwright-runtime.sh 'data:text/html,<title>SOGA-34 shell smoke</title><h1>ok</h1>'
```

The standalone interactive `playwright-cli open` path still expects a system
Chrome channel and is not the preferred proof path for SOG.

## Required base-runtime packages

These packages must exist in the Paperclip runtime image for Chromium to start:

- `libglib2.0-0`
- `libnss3`
- `libnspr4`
- `libatk1.0-0`
- `libatk-bridge2.0-0`
- `libdbus-1-3`
- `libcups2`
- `libx11-6`
- `libx11-xcb1`
- `libxcb1`
- `libxcomposite1`
- `libxdamage1`
- `libxext6`
- `libxfixes3`
- `libxrandr2`
- `libxkbcommon0`
- `libgbm1`
- `libasound2`
- `libcairo2`
- `libpango-1.0-0`
- `libatspi2.0-0`

The SOG application already documents a similar Chromium dependency set in
`agente/Dockerfile`; this script makes the runtime requirement explicit for the
Paperclip container as well.
