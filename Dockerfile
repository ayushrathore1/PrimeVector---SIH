# syntax=docker/dockerfile:1
# =============================================================================
#   SATYADH VANI 2 (PRIMEVECTOR) — PRODUCTION DOCKERFILE
#   Multi-Stage Build: Fast, Compact, Zero-Card Cloud Deployment
# =============================================================================

# ── STAGE 1: Build React 19 Frontend ─────────────────────────
FROM node:20-slim AS frontend-builder
WORKDIR /build

COPY website/package.json website/package-lock.json* ./
RUN npm install

COPY website/ ./
RUN npm run build

# ── STAGE 2: Python Microservices Runtime ────────────────────
FROM python:3.11-slim AS runner

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=10000 \
    KMP_DUPLICATE_LIB_OK=TRUE \
    SPOOF_MODEL_REGISTRY_BACKEND=dhwani \
    SPOOF_DHWANI_CHECKPOINT_PATH=/app/ml/dhwani/checkpoints/dhwani_baseline_v2.pt

# Install system audio libraries and build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Step A: Install CPU-only PyTorch first (compact ~150MB instead of 2.5GB CUDA)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Step B: Install consolidated production Python dependencies
COPY deployment/requirements-docker.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Step C: Copy Built Frontend Assets from Stage 1
COPY --from=frontend-builder /build/dist /app/website/dist

# Step D: Copy Codebase & Model Checkpoints
COPY services/ /app/services/
COPY ml/ /app/ml/
COPY deployment/ /app/deployment/
COPY test-dashboard.html /app/test-dashboard.html

# Expose public gateway port
EXPOSE ${PORT}

# Healthcheck for container orchestrators
HEALTHCHECK --interval=20s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://127.0.0.1:${PORT}/healthz || exit 1

# Launch production multi-service supervisor & reverse proxy
CMD ["python", "deployment/entrypoint.py"]
