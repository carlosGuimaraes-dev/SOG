# SOGA-36 Runtime Rebuild Verification

Date: 2026-05-31

## Objective

Verify whether the Paperclip `codex_local` runtime image was rebuilt/redeployed
from the patched `/app/Dockerfile`, and whether cached Playwright Chromium can
launch in the fresh runtime.

## What was checked

1. `/app/Dockerfile` in the runtime source
2. Tool availability in the live agent container
3. Shared-library resolution for cached Chromium
4. Repo diagnostic launcher script

## Findings

- `/app/Dockerfile` does contain the intended `production`-stage patch:
  - global `@playwright/cli@latest`
  - Debian trixie Chromium libraries such as `libglib2.0-0t64`, `libnss3`,
    `libx11-6`, `libxkbcommon0`, `libgbm1`
- The current live agent container is still running the old image:
  - `playwright-cli` is not on `PATH`
  - `docker` is not installed, so this agent cannot rebuild/redeploy the
    external runtime image from inside the current container
- Cached Chromium still fails dynamic linking:
  - `ldd /paperclip/.cache/ms-playwright/chromium-1224/chrome-linux64/chrome`
    still reports missing libraries including `libglib-2.0.so.0`,
    `libnss3.so`, `libX11.so.6`, `libxkbcommon.so.0`, `libgbm.so.1`,
    `libcairo.so.2`, `libpango-1.0.so.0`
- `./scripts/playwright-runtime.sh https://example.com` still fails with the
  same missing-library report, so real Chromium launch is not yet available in
  this runtime

## Commands

```bash
sed -n '1,220p' /app/Dockerfile
command -v docker
command -v playwright-cli
ldd /paperclip/.cache/ms-playwright/chromium-1224/chrome-linux64/chrome
./scripts/playwright-runtime.sh https://example.com
```

## Conclusion

The source patch exists, but the running Paperclip `codex_local` container has
not been rebuilt/redeployed from it yet. SOGA-36 remains blocked on the
external runtime-image rollout owned outside the SOG repo. After that rollout,
this same verification should be rerun in a fresh agent runtime:

```bash
playwright-cli --version
ldd /paperclip/.cache/ms-playwright/chromium-1224/chrome-linux64/chrome
./scripts/playwright-runtime.sh https://example.com
```
