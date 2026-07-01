# Stage 1: Build — instala dependências Python e browsers Playwright
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

# Stage 2: Runtime — imagem mínima com apenas o necessário
FROM python:3.12-slim

# Dependências de sistema mínimas para Chromium headless.
# Removidas: libcups2 (impressão), libasound2 (áudio), libatspi2.0-0 (acessibilidade),
# wget/procps (baixados no builder; healthcheck em Python puro).
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libnss3 libnspr4 libatk1.0-0 \
    libatk-bridge2.0-0 libdrm2 libxkbcommon0 \
    libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 \
    libpango-1.0-0 libcairo2 \
    fonts-liberation libfontconfig1 \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Criar usuário não-root e diretórios necessários
RUN useradd -m appuser && \
    mkdir -p /app /dados/screenshots /dados/demonstrativos /dados/auth /tmp && \
    chown -R appuser:appuser /app /dados /tmp

# Copiar venv e browsers do stage builder
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /root/.cache/ms-playwright /home/appuser/.cache/ms-playwright
RUN chown -R appuser:appuser /opt/venv /home/appuser/.cache

# Remover drivers Playwright desnecessários (macOS, Windows) para economizar espaço
RUN find /opt/venv/lib -path "*/playwright/driver*" \( -name "*.exe" -o -name "*mac*" \) -delete || true

ENV PATH="/opt/venv/bin:$PATH" \
    PLAYWRIGHT_BROWSERS_PATH=/home/appuser/.cache/ms-playwright \
    PYTHONUNBUFFERED=1

# Copiar aplicação
COPY --chown=appuser:appuser agente/src/ /app/src/

USER appuser
WORKDIR /app

# Healthcheck em Python puro — verifica se o serviço longo continua como PID 1
RUN printf '%s\n' \
    'from pathlib import Path' \
    'cmdline = Path("/proc/1/cmdline").read_bytes()' \
    'raise SystemExit(0 if b"servico.py" in cmdline else 1)' > /app/healthcheck.py

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python /app/healthcheck.py

CMD ["python", "/app/src/servico.py"]

FROM python:3.12-slim AS qa

RUN useradd -m appuser && mkdir -p /app /fixtures && chown -R appuser:appuser /app /fixtures

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /root/.cache/ms-playwright /home/appuser/.cache/ms-playwright
RUN chown -R appuser:appuser /opt/venv /home/appuser/.cache

ENV PATH="/opt/venv/bin:$PATH" \
    PLAYWRIGHT_BROWSERS_PATH=/home/appuser/.cache/ms-playwright \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src:/app/shared

WORKDIR /app

COPY agente/requirements-dev.txt /tmp/requirements-dev.txt
RUN pip install --no-cache-dir -r /tmp/requirements-dev.txt

COPY --chown=appuser:appuser agente/src/ /app/src/
COPY --chown=appuser:appuser agente/tests/ /app/tests/
COPY --chown=appuser:appuser agente/scripts/ /app/scripts/
COPY --chown=appuser:appuser shared/ /app/shared/

USER appuser

CMD ["pytest", "-q", "/app/tests/test_extrator_pdf.py"]
