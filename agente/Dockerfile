FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget gnupg libglib2.0-0 libnss3 libnspr4 libatk1.0-0 \
    libatk-bridge2.0-0 libcups2 libdrm2 libdbus-1-3 libxkbcommon0 \
    libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 \
    libpango-1.0-0 libcairo2 libasound2 libatspi2.0-0 \
    fonts-liberation libfontconfig1 cron \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY agente/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN playwright install chromium
RUN playwright install-deps chromium

COPY agente/src/ ./src/
COPY agente/crontab /etc/cron.d/custas-cron
RUN chmod 0644 /etc/cron.d/custas-cron && crontab /etc/cron.d/custas-cron

RUN mkdir -p /dados/screenshots /dados/demonstrativos

CMD python /app/src/main.py && cron -f
