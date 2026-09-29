# ------------------------------------------------------------------------------
# Stage 1: Build stage using uv
# ------------------------------------------------------------------------------
FROM python:3.14-slim-bookworm AS builder

# Install uv binary from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy root workspace manifests and dependent packages for layer caching
COPY pyproject.toml uv.lock ./
COPY packages/common-auth/ packages/common-auth/
COPY services/user-service/ services/user-service/
COPY services/storage-service/pyproject.toml services/storage-service/

# Install user-service and its workspace dependencies into /app/.venv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable --package user-service

# ------------------------------------------------------------------------------
# Stage 2: Minimal Production Runtime
# ------------------------------------------------------------------------------
FROM python:3.14-slim-bookworm AS runner

ENV PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/services/user-service/src"

WORKDIR /app/services/user-service

# Security: Run as non-root user (Kubernetes & EKS best practice)
RUN groupadd --gid 10001 appuser && \
    useradd --uid 10001 --gid 10001 -m -s /bin/bash appuser

# Copy virtual environment and application code from builder
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --from=builder --chown=appuser:appuser /app/packages /app/packages
COPY --from=builder --chown=appuser:appuser /app/services/user-service /app/services/user-service

USER appuser

EXPOSE 8000

# Default command: start FastAPI application with uvicorn
CMD ["uvicorn", "user_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
