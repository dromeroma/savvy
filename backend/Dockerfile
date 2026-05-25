# ---------- build stage ----------
FROM python:3.12-slim AS builder

WORKDIR /build

# Build deps required to compile pycairo (transitive dep of xhtml2pdf via
# svglib → rlpycairo). pycairo has no manylinux wheel — must be built from
# source against the system cairo headers.
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        pkg-config \
        libcairo2-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --prefix=/install .

COPY src ./src

# ---------- runtime stage ----------
FROM python:3.12-slim AS runtime

WORKDIR /app

# Runtime cairo shared library (NOT the -dev headers — just the .so files
# pycairo loads via ctypes at import time).
RUN apt-get update && apt-get install -y --no-install-recommends \
        libcairo2 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY src ./src
COPY pyproject.toml ./
COPY alembic.ini* ./

# Non-root user
RUN addgroup --system savvy && adduser --system --ingroup savvy savvy
USER savvy

EXPOSE 8000

# 1 worker keeps memory under Render's 512MB starter tier limit.
# Uvicorn handles concurrency via asyncio inside the single worker — for a
# small SaaS with light traffic, 1 worker is plenty. Scale via instance size
# or worker count once traffic justifies it.
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
