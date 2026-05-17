FROM python:3.12-slim

WORKDIR /app

COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ ./shared/
RUN pip install -e ./shared

COPY api/src/ ./src/

EXPOSE 8000

ENV PYTHONPATH=/app/src
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
