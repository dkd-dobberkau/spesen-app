# Multi-stage build für kleineres Image
FROM python:3.11-slim AS builder

WORKDIR /app

# System-Dependencies für Build
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# uv installieren
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Dependencies installieren
COPY pyproject.toml .
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

# Production Image
FROM python:3.11-slim

# System-Dependencies für Runtime (Tesseract, Poppler)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-deu \
    tesseract-ocr-eng \
    poppler-utils \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root User erstellen
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Python packages vom Builder kopieren
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# App-Code kopieren
COPY --chown=appuser:appuser app.py cli.py ./
COPY --chown=appuser:appuser templates/ ./templates/

# Verzeichnisse für Daten
RUN mkdir -p /app/data /app/exports && chown -R appuser:appuser /app

USER appuser

# Environment
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py

# Health Check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

EXPOSE 5000

CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]
