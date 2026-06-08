# PREMONITION ML System — production Docker image
# Multi-stage build for smaller final image

# ── Stage 1: Builder ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

LABEL maintainer="PREMONITION Team"
LABEL description="AI early-warning system for ICU patient deterioration"
LABEL version="0.1.0"

WORKDIR /app

# System deps for matplotlib / SHAP
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY pyproject.toml .
COPY src/ src/
COPY scripts/ scripts/
COPY data/raw/ data/raw/
COPY infra/ infra/

# Install package in editable mode
RUN pip install --no-cache-dir -e . --no-deps

# Create runtime directories
RUN mkdir -p data/processed models/artifacts reports logs logs/predictions backups

# Non-root user for security
RUN useradd --create-home --shell /bin/bash premonition
RUN chown -R premonition:premonition /app
USER premonition

# Environment defaults
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PREMONITION_DATA_RAW=/app/data/raw \
    PREMONITION_DATA_PROCESSED=/app/data/processed \
    PREMONITION_MODELS_DIR=/app/models/artifacts \
    PREMONITION_REPORTS_DIR=/app/reports \
    PREMONITION_LOGS_DIR=/app/logs \
    PREMONITION_LOG_LEVEL=INFO

# Health check — verify Python and package import
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import premonition; print('ok')" || exit 1

ENTRYPOINT ["python", "scripts/docker_entrypoint.py"]
CMD ["help"]
