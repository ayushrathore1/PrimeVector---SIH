FROM python:3.11-slim

WORKDIR /app

# Install libsndfile for librosa audio loading
RUN apt-get update && apt-get install -y --no-install-recommends libsndfile1 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

WORKDIR /app/app
ENV PYTHONPATH=/app/app:/app

# Avoid OpenMP duplicate library crash on some builds
ENV KMP_DUPLICATE_LIB_OK=TRUE

EXPOSE 8002

# Default to trained deepfake model
ENV SPOOF_MODEL_REGISTRY_BACKEND=deepfake

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
