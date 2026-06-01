# Stage 1: Build — instala dependências Python, browsers Playwright e supercronic
FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY agente/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium

COPY shared/ ./shared/
RUN pip install --no-cache-dir ./shared

# Baixar supercronic no builder para evitar wget no runtime
ARG SUPERCRONIC_URL=https://github.com/aptible/supercronic/releases/download/v0.2.43/supercronic-linux-amd64
ARG SUPERCRONIC_SHA1SUM=f97b92132b61a8f827c3faf67106dc0e4467ccf2
RUN wget -q "$SUPERCRONIC_URL" -O /tmp/supercronic && \
    echo "${SUPERCRONIC_SHA1SUM}  /tmp/supercronic" | sha1sum -c - && \
    chmod +x /tmp/supercronic

# Stage 2: Runtime — imagem mínima com apenas o necessário
FROM python:3.12-slim

# Dependências de sistema mínimas para Chromium headless.
# wget/procps ficam fora do runtime; o healthcheck usa Python puro.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libnss3 libnspr4 libatk1.0-0 \
    libatk-bridge2.0-0 libatspi2.0-0t64 libdrm2 libxkbcommon0 \
    libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 \
    libpango-1.0-0 libcairo2 \
    libcups2t64 libasound2t64 \
    fonts-liberation libfontconfig1 \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Criar usuário não-root e diretórios necessários
RUN useradd -m appuser && \
    mkdir -p /app /dados/screenshots /dados/demonstrativos /tmp && \
    chown -R appuser:appuser /app /dados /tmp

# Copiar venv, browsers e supercronic do stage builder
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /root/.cache/ms-playwright /home/appuser/.cache/ms-playwright
COPY --from=builder /tmp/supercronic /usr/local/bin/supercronic
RUN chown -R appuser:appuser /opt/venv /home/appuser/.cache

ENV PATH="/opt/venv/bin:$PATH" \
    PLAYWRIGHT_BROWSERS_PATH=/home/appuser/.cache/ms-playwright \
    PYTHONUNBUFFERED=1

# Copiar aplicação e crontab com permissões restritas
COPY --chown=appuser:appuser agente/src/ /app/src/
COPY --chown=appuser:appuser agente/crontab /app/crontab
RUN chmod 0600 /app/crontab

USER appuser
WORKDIR /app

# Healthcheck em Python puro — verifica se o serviço longo do agente está rodando.
RUN printf '%s\n' \
    'import os, sys' \
    'for pid in os.listdir("/proc"):' \
    '    if pid.isdigit():' \
    '        try:' \
    '            with open(f"/proc/{pid}/cmdline", "rb") as f:' \
    '                cmdline = f.read()' \
    '                if b"/app/src/servico.py" in cmdline:' \
    '                    sys.exit(0)' \
    '        except Exception:' \
    '            pass' \
    'sys.exit(1)' > /app/healthcheck.py

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python /app/healthcheck.py

CMD ["python", "/app/src/servico.py"]
