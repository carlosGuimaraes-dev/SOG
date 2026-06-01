# SOGA-33 — Playwright CLI, Chromium and E2E Skills Setup

## Scope

Install the Playwright agent CLI requested from the official Playwright Agent CLI flow, add local E2E skill files, and verify whether browser automation can run in the current Paperclip workspace.

## Installed

- Playwright CLI package: `@playwright/cli@latest`
- Installed command path: `$AGENT_HOME/.npm-global/bin/playwright-cli`
- CLI version observed: `0.1.13`
- Playwright core version reported by `install-browser --list`: `1.61.0-alpha-1778188671000`
- Browser cache path: `/paperclip/.cache/ms-playwright`
- Chromium cache entry: `/paperclip/.cache/ms-playwright/chromium-1224`
- Agent skill bundle:
  - `.agents/skills/playwright-cli/`
  - `.claude/skills/playwright-cli/`

## Verification

Commands executed:

```bash
$AGENT_HOME/.npm-global/bin/playwright-cli --version
$AGENT_HOME/.npm-global/bin/playwright-cli install --skills=agents
$AGENT_HOME/.npm-global/bin/playwright-cli install-browser --list
```

Results:

- CLI is installed and responds.
- E2E skill files are present for agent workflows.
- Chromium cache is listed by Playwright.

## Runtime Status

Updated after the board/user unblock comment on 2026-05-31:

- Linux dependencies required for Chromium were installed in the Paperclip/SOG container.
- `chromium_headless_shell` is present in the persistent Playwright cache:
  - `/paperclip/.cache/ms-playwright/chromium_headless_shell-1208`
- A real headless smoke was verified as the `node` user:

```bash
node -e "const { chromium } = require('/app/node_modules/.pnpm/playwright-core@1.58.2/node_modules/playwright-core'); (async () => { const browser = await chromium.launch({ headless: true }); const page = await browser.newPage(); await page.goto('data:text/html,<title>SOGA-33 smoke</title><h1>ok</h1>'); const title = await page.title(); await browser.close(); console.log('chromium.launch headless smoke:', title); })().catch(err => { console.error(err); process.exit(1); });"
```

Result:

```text
chromium.launch headless smoke: SOGA-33 smoke
```

For smoke/E2E headless validation, Playwright plus Chromium headless are now working in the Paperclip container.

## Standalone `playwright-cli open` Resolution

The standalone `playwright-cli open` path does not accept a `--headless` flag. It is headless by default; the flag only exists in the opposite direction as `--headed`.

The default browser path uses system Chrome and fails if `/opt/google/chrome/chrome` is absent. The practical fix is to install Playwright's Chrome-for-Testing artifact and open with `--browser chromium`.

The CLI installer command identified the missing artifact:

```bash
$AGENT_HOME/.npm-global/bin/playwright-cli open about:blank --browser chromium --json
```

Initial result:

```text
Browser "chrome-for-testing" is not installed. Run `playwright-cli install-browser chrome-for-testing` to install
```

Because the installer still hung after download in this runner, the artifact was installed manually into Playwright's expected cache path:

```bash
rm -rf /paperclip/.cache/ms-playwright/chromium-1224 /tmp/pw-cft-1224.zip
curl -L --fail --retry 3 -o /tmp/pw-cft-1224.zip https://cdn.playwright.dev/builds/cft/149.0.7827.3/linux64/chrome-linux64.zip
mkdir -p /paperclip/.cache/ms-playwright/chromium-1224
python3 -m zipfile -e /tmp/pw-cft-1224.zip /paperclip/.cache/ms-playwright/chromium-1224
touch /paperclip/.cache/ms-playwright/chromium-1224/INSTALLATION_COMPLETE
chmod +x /paperclip/.cache/ms-playwright/chromium-1224/chrome-linux64/chrome /paperclip/.cache/ms-playwright/chromium-1224/chrome-linux64/chrome_crashpad_handler
rm -f /tmp/pw-cft-1224.zip
```

Verification:

```bash
/paperclip/.cache/ms-playwright/chromium-1224/chrome-linux64/chrome --version
$AGENT_HOME/.npm-global/bin/playwright-cli open about:blank --browser chromium --json
$AGENT_HOME/.npm-global/bin/playwright-cli close --json
```

Observed result:

```text
Google Chrome for Testing 149.0.7827.3
{
  "session": "default",
  "pid": 4554,
  "result": {
    "snapshot": {
      "file": ".playwright-cli/page-2026-05-31T22-52-58-974Z.yml"
    }
  }
}
```

Final guidance:

- Use `playwright-cli open <url> --browser chromium` for the standalone CLI path.
- Do not pass `--headless`; default CLI open is already headless.
- Use `--headed` only when visual headed mode is needed.

Earlier observed failures before the runtime fix:

- Direct Chromium executable launch failed because the runtime image was missing native browser libraries, starting with `libglib-2.0.so.0`.
- `apt-get update` could not run as the current `node` user due lack of permission on `/var/lib/apt/lists/partial`.
- `playwright-cli install-browser chrome` attempted to switch to root for dependencies and failed with `su: Authentication failure`.

## Technical Conclusion

The CLI and skills installation part of SOGA-33 is complete in the workspace, Chromium headless is cached, and real headless browser launch now works in the Paperclip runtime. Future SOG UI verification can produce browser evidence through Playwright headless smoke/E2E flows.
