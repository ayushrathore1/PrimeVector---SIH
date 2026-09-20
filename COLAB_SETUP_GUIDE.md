# 🛡️ Google Colab Hybrid Setup Guide

Run the Satya PrimeVector platform on your **8 GB RAM PC** by running the **Deepfake Detection Model (`spoof-detection-service`) LOCALLY** on your PC while offloading heavy PyTorch spectrogram feature extraction and speaker enrollment to a **free Google Colab** GPU runtime.

**Local RAM usage: ~350 MB** (instead of 5+ GB with Docker)

---

## Architecture

```
Your Local PC (~350 MB RAM)                   Google Colab (Free 12 GB RAM)
┌──────────────────────────────────────┐      ┌──────────────────────────┐
│ spoof-detection (Dhwani 2)     :8002 │      │ feature-extraction :8001 │
│ api-gateway                    :8090 │  ← ngrok → │ enrollment         :8003 │
│ risk-fusion-engine             :8000 │   tunnel   │ reverse-proxy      :9090 │
│ policy-threshold-engine        :8004 │              └──────────────────────────┘
│ alerting-service               :8005 │
│ orchestrator                   :8085 │
│ dashboard                      :9000 │
└──────────────────────────────────────┘
```

---

## Step-by-Step Setup

### Step 1: Get a Free ngrok Auth Token (one-time, 30 seconds)

1. Go to [ngrok.com/signup](https://dashboard.ngrok.com/signup) and create a free account
2. Go to [Your Authtoken](https://dashboard.ngrok.com/get-started/your-authtoken)
3. Copy the token (looks like `2abc...xyz`)

### Step 2: Start Heavy ML Services on Google Colab

1. Open [Google Colab](https://colab.research.google.com)
2. Create a **New Notebook**
3. In the first cell, paste:

```python
# Download and run the PrimeVector Colab launcher
!rm -f colab_ml_services.py
!wget -q -O colab_ml_services.py https://raw.githubusercontent.com/ayushrathore1/PrimeVector---SIH/local-model-integration/colab_ml_services.py

import sys
if 'colab_ml_services' in sys.modules:
    del sys.modules['colab_ml_services']

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

### Step 3: Configure & Run Your Local PC

Run the single master hybrid launcher:

```bash
python run_local_lightweight.py
```

If `COLAB_TUNNEL_URL` is not found in `.env`, the script will prompt you interactively in the terminal to paste your URL and save it automatically!

---

## What Runs Where?

| Service | Location | RAM Used | Purpose |
|:---|:---|:---|:---|
| **spoof-detection-service** | 💻 Local | ~80 MB | Local Dhwani 2 Deepfake Classifier (Sub-50ms CPU) |
| **api-gateway** | 💻 Local | ~45 MB | Public REST API, API Keys & Metering |
| **risk-fusion-engine** | 💻 Local | ~40 MB | Deterministic Compliance & Risk Math |
| **policy-threshold-engine**| 💻 Local | ~40 MB | Configurable Thresholds & Auto-Block Gate |
| **alerting-service** | 💻 Local | ~40 MB | Real-time Webhooks & Alerts |
| **orchestrator** | 💻 Local | ~60 MB | Call Pipeline Coordinator |
| **dashboard** | 💻 Local | ~20 MB | Static Web UI |
| **feature-extraction** | ☁️ Colab | ~500 MB (Colab) | Log-Mel Spectrogram Extraction |
| **enrollment-service** | ☁️ Colab | ~450 MB (Colab) | Resemblyzer Voiceprint Embeddings |

**Total Local RAM: ~350 MB** ✅

---

## FAQ & Loose Ends Covered

### Why run the Deepfake Model locally?
Dhwani 2 is a compact ~6M parameter model optimized for CPU inference (<50ms execution). Running it locally eliminates ngrok tunnel roundtrips for deepfake detection while keeping heavy feature extraction and speaker enrollment on Colab's 12 GB GPU runtime.

### What about ngrok browser warning pages?
`run_local_lightweight.py` and the `orchestrator` automatically inject the `ngrok-skip-browser-warning: true` header into all HTTP requests, preventing HTML interstitial errors.

### What if the ngrok URL changes?
Each time you restart Colab, ngrok assigns a new URL. Simply run `python run_local_lightweight.py` — it will detect an invalid/missing URL and prompt you to paste the new one, saving it to `.env` instantly.
