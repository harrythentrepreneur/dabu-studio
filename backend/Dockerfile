# Multi-stage Dockerfile for RunPod serverless deployment (default)
# Optimized for Express Builder (no browser automation)

# Stage 1: Builder
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    cmake \
    wget \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements first for better caching
COPY requirements.txt /tmp/
COPY requirements-runpod.txt /tmp/
# Also copy nested requirements referenced by requirements.txt
RUN mkdir -p /tmp/runpod/worker
COPY runpod/worker/requirements.txt /tmp/runpod/worker/requirements.txt

# Install Python dependencies with optimizations
# Install minimal deps (builder only)
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

# Install runtime dependencies for heavy processing
RUN apt-get update && apt-get install -y \
    # FFmpeg for video processing
    ffmpeg \
    # Minimal runtime deps (no Playwright/browser)
    libnss3 \
    libnspr4 \
    libasound2 \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy heavy requirement files from builder and install
COPY --from=builder /tmp/requirements-runpod.txt /tmp/requirements-runpod.txt
COPY --from=builder /tmp/runpod/worker/requirements.txt /tmp/runpod/worker/requirements.txt

# Install heavy runtime dependencies
RUN pip install --no-cache-dir -r /tmp/requirements-runpod.txt && \
    pip install --no-cache-dir -r /tmp/runpod/worker/requirements.txt

# Copy rest of application code
COPY . /app/

# Create necessary directories
RUN mkdir -p /app/temp \
    /app/output \
    /app/logs \
    /app/uploads

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENVIRONMENT_MODE=PRODUCTION \
    RUNPOD_DEBUG_LEVEL=INFO

# Health check (optional)
EXPOSE 8000

# Default command: RunPod worker entrypoint
CMD ["python", "-u", "runpod/worker/main_handler.py"]
