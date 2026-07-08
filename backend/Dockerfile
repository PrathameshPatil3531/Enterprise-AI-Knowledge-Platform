# ==============================================================================
# Backend Dockerfile — Multi-Stage Build
#
# WHY multi-stage build?
# - Stage 1 (base): system dependencies
# - Stage 2 (dependencies): Python packages (cached separately from app code)
# - Stage 3 (app): application code
#
# Benefit: Changing app code only invalidates Stage 3 cache.
# Docker doesn't re-install all Python packages on every code change.
# This makes CI/CD builds 5-10x faster.
# ==============================================================================

# ==============================================================================
# Stage 1 — Base: Python runtime + system libraries
# ==============================================================================
FROM python:3.12-slim AS base

# PYTHONDONTWRITEBYTECODE=1  → Don't create .pyc files (saves space in image)
# PYTHONUNBUFFERED=1         → Don't buffer stdout/stderr (essential for Docker logs)
# PYTHONPATH=/app            → Makes `from app.xxx import` work from any directory
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# System packages:
# - gcc        : C compiler (required to build some Python packages from source)
# - libpq-dev  : PostgreSQL client headers (required by psycopg2)
# - curl       : Used for health check commands in docker-compose
# - --no-install-recommends: Keep image size small
# - rm -rf /var/lib/apt/lists/*: Clean apt cache to reduce image size
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ==============================================================================
# Stage 2 — Dependencies: Install Python packages
#
# Copying requirements.txt BEFORE copying application code means:
# - Docker caches this layer separately
# - If only app code changes, this expensive layer is reused from cache
# - pip install only re-runs when requirements.txt changes
# ==============================================================================
FROM base AS dependencies

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ==============================================================================
# Stage 3 — Application: Copy code and configure runtime
# ==============================================================================
FROM dependencies AS app

# Copy application code (changes frequently — separate layer from dependencies)
COPY . .

# Create uploads directory for document storage
# In production, this would be a mounted volume or cloud storage (S3)
RUN mkdir -p /app/uploads && chmod 755 /app/uploads

# Create a non-root user for security
# Running containers as root is a security risk
RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup appuser && \
    chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

# Production startup command (no --reload in production)
# In development, docker-compose.dev.yml overrides this with --reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
