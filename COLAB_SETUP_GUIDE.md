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

## 👥 How to Share Setup with Teammates

There are **two ways** to share this setup with your team:

### Method A: Share YOUR Live Colab Tunnel (Fastest — 1-minute setup for teammate)

If **YOU** already have Google Colab running with ngrok:

1. **You copy your active ngrok URL** from your `.env` file:
   ```env
   COLAB_TUNNEL_URL=https://headgear-residual-wooing.ngrok-free.dev
   ```
2. **Send that URL to your teammate** (via WhatsApp / Discord / Slack).
3. **Teammate's local setup**:
   - Clones repo: `git clone -b local-model-integration https://github.com/ayushrathore1/PrimeVector---SIH.git`
   - Installs lightweight packages: `pip install fastapi uvicorn pydantic httpx requests`
   - Paste the shared URL in their `.env`:
     ```env
     COLAB_TUNNEL_URL=https://headgear-residual-wooing.ngrok-free.dev
     ```
   - Runs `python run_local_lightweight.py`
4. **Done!** Both of you can hit your active Colab ML backend simultaneously without your teammate needing a Google Colab or ngrok account.

---

### Method B: Teammate Runs Their Own Colab + Own/Shared ngrok Token

If your teammate wants to run their own Colab GPU instance independently:

1. **Get GitHub Personal Access Token (PAT)** (required because the repo is private):
   - Teammate creates a token at [github.com/settings/tokens](https://github.com/settings/tokens) with `repo` scope.

2. **In Google Colab**, paste and run this cell:
   ```python
   # 1. Download launcher from branch
   !wget -q -O colab_ml_services.py https://raw.githubusercontent.com/ayushrathore1/PrimeVector---SIH/local-model-integration/colab_ml_services.py

   # 2. Run launcher (pass PAT for private repo access & ngrok token)
   from colab_ml_services import main

   main(
       ngrok_auth_token="YOUR_OR_TEAMMATE_NGROK_TOKEN",
       github_pat="TEAMMATE_GITHUB_PAT",
       branch="local-model-integration"
   )
   ```
   *Note: Teammate can use their own free ngrok token from [ngrok.com](https://dashboard.ngrok.com) OR use your ngrok auth token.*

3. **Teammate configures local `.env`**:
   - Copy the new ngrok URL printed by Colab into their `.env`:
     ```env
     COLAB_TUNNEL_URL=https://xxxx-xx-xx-xx.ngrok-free.app
     ```
   - Run `python run_local_lightweight.py` on their machine.

---

## Troubleshooting

| Issue | Solution |
|:---|:---|
| "COLAB_TUNNEL_URL not found" | Add the ngrok URL to your `.env` file |
| "Colab tunnel NOT reachable" | Check Colab tab is still running; re-run notebook if timed out |
| ngrok "ERR_NGROK_108" | Free tier limit reached — wait 60 seconds and try again |
| Private repo clone error on Colab | Pass `github_pat="ghp_xxx"` to `main(...)` in the Colab cell |
| Services unhealthy on Colab | Check Colab cell output or `/content/*.log` files in Colab |
| Port already in use locally | Kill existing processes: `taskkill /F /IM python.exe` (Windows) |
