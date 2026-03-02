# ───────────────────────────────────────────────────────────────
# Stage 1 – builder: install Python dependencies
# ───────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# System build deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv from PyPI (no external container registry required)
RUN pip install --no-cache-dir uv

# Install Python deps into the system site-packages
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

# ───────────────────────────────────────────────────────────────
# Stage 2 – runtime: lean production image
# ───────────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# Sane Python defaults for containers
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Only the runtime libs we actually need
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Pull installed packages from the builder
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /usr/local/bin /usr/local/bin

# Non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Copy source
COPY --chown=appuser:appgroup . .

# Entrypoint script
COPY --chown=appuser:appgroup scripts/docker.sh /usr/local/bin/docker.sh
RUN chmod +x /usr/local/bin/docker.sh

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["docker.sh"]
