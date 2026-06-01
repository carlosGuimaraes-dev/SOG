# SOGA-36 Tech Lead Runtime Rebuild Blocker

Date: 2026-05-31

## Finding

The source patch is present in `/app/Dockerfile`, but the active `codex_local`
agent container is still running the old Paperclip runtime image.

This heartbeat verified:

```sh
command -v playwright-cli
command -v docker
command -v podman
find / -maxdepth 4 \( -name docker.sock -o -name podman.sock -o -name containerd.sock \) 2>/dev/null
ldd /paperclip/.cache/ms-playwright/chromium-1224/chrome-linux64/chrome
```

Results:

- `playwright-cli` is not on `PATH`.
- `docker` is not installed.
- `podman` is not installed.
- No Docker, Podman, or containerd socket is mounted into the agent runtime.
- `ldd` still reports the Chromium library set as missing, including
  `libglib-2.0.so.0`, `libnss3.so`, `libX11.so.6`, `libxkbcommon.so.0`,
  `libgbm.so.1`, `libcairo.so.2`, and `libpango-1.0.so.0`.

## Consequence

No SOG agent can complete the acceptance criteria from inside the current
runtime. All project agents use the same `codex_local` adapter, so delegating
another verification issue before the image is rebuilt would only reproduce the
same old-image failure.

## Required Unblock Action

A Paperclip platform operator or board user with host Docker/container runtime
access must rebuild and redeploy the Paperclip runtime image from the patched
`/app/Dockerfile`, preserving the existing `/paperclip` data volume and runtime
environment.

For the documented Docker quickstart deployment, the host-level command is:

```sh
docker compose -f docker/docker-compose.quickstart.yml up -d --build
```

For the documented manual Docker deployment, the equivalent host-level sequence
is:

```sh
docker build -t paperclip-local .
docker rm -f paperclip
docker run --name paperclip \
  -p 3100:3100 \
  -e HOST=0.0.0.0 \
  -e PAPERCLIP_HOME=/paperclip \
  -v "$(pwd)/data/docker-paperclip:/paperclip" \
  paperclip-local
```

The actual operator should use the deployment's existing env file, secrets, port
mapping, and volume path rather than replacing them with placeholders.

## Post-Rebuild Verification

After redeploying, wake a fresh `codex_local` agent runtime and run:

```sh
playwright-cli --version
ldd /paperclip/.cache/ms-playwright/chromium-1224/chrome-linux64/chrome | grep 'not found'
playwright-cli open about:blank
```

Acceptance requires the CLI version command to succeed, `ldd` to show no missing
libraries for Chromium, and a real browser launch to succeed.

## 2026-05-31 Follow-up Heartbeat

Run `eea4cf38-bd70-4c2a-8aaa-f36605772112` rechecked the smallest acceptance
probes in a fresh Tech Lead heartbeat.

```sh
command -v playwright-cli || true
command -v docker || true
command -v podman || true
find / -maxdepth 4 \( -name docker.sock -o -name podman.sock -o -name containerd.sock \) 2>/dev/null | head -20
ldd /paperclip/.cache/ms-playwright/chromium-1224/chrome-linux64/chrome | grep 'not found' || true
```

Results remain unchanged:

- `playwright-cli` is still absent from `PATH`.
- `docker` and `podman` are still absent.
- no Docker, Podman, or containerd socket is mounted into this runtime.
- Chromium still reports the old-image missing shared libraries, including
  `libglib-2.0.so.0`, `libnss3.so`, `libX11.so.6`, `libxkbcommon.so.0`,
  `libgbm.so.1`, `libcairo.so.2`, and `libpango-1.0.so.0`.

The issue state also drifted back to `in_progress` even though the blocker was
recorded. This heartbeat corrected the disposition back to `blocked`; no new
same-runtime child issue was created because it would reproduce the same
container authority failure.
