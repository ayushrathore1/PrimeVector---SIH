# 🛡️ Google Colab Hybrid Setup Guide

Run the Satya PrimeVector platform on your **8 GB RAM PC** by offloading heavy ML services to a **free Google Colab** runtime.

**Local RAM usage: ~300 MB** (instead of 5+ GB with Docker)

---

## Architecture

```
Your PC (~300 MB RAM)                Google Colab (Free 12 GB RAM)
┌──────────────────────┐             ┌──────────────────────────┐
│ risk-fusion    :8000 │             │ feature-extraction :8001 │
│ policy-engine  :8004 │  ← ngrok → │ spoof-detection    :8002 │
│ alerting       :8005 │   tunnel   │ enrollment         :8003 │
│ orchestrator   :8080 │             │ reverse-proxy      :9090 │
│ dashboard      :9000 │             └──────────────────────────┘
└──────────────────────┘
```

---

## Step-by-Step Setup

### Step 1: Get a Free ngrok Auth Token (one-time, 30 seconds)

1. Go to [ngrok.com/signup](https://dashboard.ngrok.com/signup) and create a free account
2. Go to [Your Authtoken](https://dashboard.ngrok.com/get-started/your-authtoken)
3. Copy the token (looks like `2abc...xyz`)

### Step 2: Start ML Services on Google Colab

1. Open [Google Colab](https://colab.research.google.com)
2. Create a **New Notebook**
3. In the first cell, paste:

```python
# Download and run the PrimeVector Colab launcher
!wget -q https://raw.githubusercontent.com/ayushrathore1/PrimeVector---SIH/main/colab_ml_services.py

from colab_ml_services import main
main(ngrok_auth_token="PASTE_YOUR_NGROK_TOKEN_HERE")
```

4. Click **Run** (▶) and wait ~2 minutes for setup
5. You'll see output like:

```
  🎉 NGROK TUNNEL IS LIVE!
  
  Public URL: https://abc123.ngrok-free.app
  
  COPY THIS INTO YOUR LOCAL .env FILE:
  COLAB_TUNNEL_URL=https://abc123.ngrok-free.app
```

6. **Copy the URL** — you'll need it next

### Step 3: Configure Your Local PC

1. Open `.env` file in your project root
2. Add the Colab tunnel URL:

```
COLAB_TUNNEL_URL=https://abc123.ngrok-free.app
```

### Step 4: Start Local Services

```bash
python run_local_lightweight.py
```

That's it! The dashboard opens at http://localhost:9000

---

## What Runs Where?

| Service | Location | RAM Used | Why |
|:---|:---|:---|:---|
| feature-extraction | ☁️ Colab | ~500 MB (on Colab) | Uses PyTorch + Resemblyzer |
| enrollment | ☁️ Colab | ~450 MB (on Colab) | Uses PyTorch + Resemblyzer |
| spoof-detection | ☁️ Colab | ~80 MB (on Colab) | Grouped with ML services |
| risk-fusion-engine | 💻 Local | ~40 MB | Pure Python, no ML |
| policy-threshold | 💻 Local | ~40 MB | Pure Python, no ML |
| alerting-service | 💻 Local | ~40 MB | Pure Python, no ML |
| orchestrator | 💻 Local | ~60 MB | HTTP client only |
| dashboard | 💻 Local | ~20 MB | Static file server |

**Total local: ~250-300 MB** ✅

---

## FAQ

### How long does a Colab session last?
Free Colab sessions last **~12 hours** max, or disconnect after **~90 minutes idle**. Keep the tab open and interact with it occasionally. For demos and development, this is plenty.

### What if the ngrok URL changes?
Each time you restart the Colab notebook, ngrok assigns a new URL. Just update `COLAB_TUNNEL_URL` in your `.env` file and restart `run_local_lightweight.py`.

### Can I still run everything locally with Docker?
Yes! The original `docker-compose up` and `start_project.py` still work exactly as before. The Colab hybrid mode is an **additional option**, not a replacement.

### What about the ingestion-gateway (Go/gRPC)?
The ingestion-gateway is standalone and not required for the demo pipeline. If needed, run it separately with `go run` locally — it uses only ~15 MB RAM.

### Do I need to install anything locally?
You need Python 3.11+ and these pip packages for the local services:
```bash
pip install fastapi uvicorn pydantic httpx
```
The heavy packages (PyTorch, Resemblyzer, librosa) are **NOT needed locally** — they run on Colab.

---

## Troubleshooting

| Issue | Solution |
|:---|:---|
| "COLAB_TUNNEL_URL not found" | Add the ngrok URL to your `.env` file |
| "Colab tunnel NOT reachable" | Check Colab tab is still running; re-run notebook if timed out |
| ngrok "ERR_NGROK_108" | Free tier limit reached — wait 60 seconds and try again |
| Services unhealthy on Colab | Check Colab cell output or `/content/*.log` files in Colab |
| Port already in use locally | Kill existing processes: `taskkill /F /IM python.exe` (Windows) |
