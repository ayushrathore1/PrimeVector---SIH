#!/usr/bin/env python3
"""
==========================================================================
  SATYA PRIMEVECTOR — GOOGLE COLAB ML SERVICES LAUNCHER
==========================================================================
  Run this script in a Google Colab notebook to host the 3 heavy ML
  microservices (feature-extraction, enrollment, spoof-detection) on
  Colab's free 12GB RAM runtime.

  A single reverse-proxy + ngrok tunnel exposes all 3 services through
  one URL (compatible with ngrok free tier — 1 tunnel).

  USAGE (in Colab):
    1. Paste this entire file into a single Colab cell
    2. Run the cell
    3. Copy the printed ngrok URL into your local .env file
    4. Run `python run_local_lightweight.py` on your PC

  The orchestrator on your PC will route ML requests to Colab via the
  ngrok tunnel. Your PC uses ~300 MB RAM instead of 5+ GB.
==========================================================================
"""

import subprocess
import sys
import os
import time
import signal
import threading

# ──────────────────────────────────────────────────────────────────────────
# STEP 1: Install dependencies
# ──────────────────────────────────────────────────────────────────────────

def install_dependencies():
    """Install all required packages for the 3 ML services + proxy."""
    print("=" * 70)
    print("  📦 STEP 1: Installing dependencies...")
    print("=" * 70)

    packages = [
        # Core web framework
        "fastapi", "uvicorn[standard]", "pydantic", "pydantic-settings",
        # HTTP proxy
        "httpx",
        # ML / Audio
        "numpy", "librosa", "resemblyzer",
        # Telemetry (feature-extraction uses it)
        "opentelemetry-api", "opentelemetry-sdk",
        # ngrok tunnel
        "pyngrok",
        # Testing (needed by some imports)
        "pytest", "hypothesis",
    ]

    # Install CPU-only PyTorch first (saves ~1.5 GB vs full CUDA torch)
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", "-q",
        "torch", "--index-url", "https://download.pytorch.org/whl/cpu"
    ])

    subprocess.check_call([
        sys.executable, "-m", "pip", "install", "-q", *packages
    ])
    print("  ✅ All dependencies installed.\n")


# ──────────────────────────────────────────────────────────────────────────
# STEP 2: Clone the repository
# ──────────────────────────────────────────────────────────────────────────

REPO_URL = "https://github.com/ayushrathore1/PrimeVector---SIH.git"
REPO_DIR = "/content/PrimeVector"

def clone_repo(github_pat=None, branch="local-model-integration"):
    """Clone the repo (handling private repos with PAT) and checkout specified branch."""
    print("=" * 70)
    print("  📁 STEP 2: Cloning repository...")
    print("=" * 70)

    url = REPO_URL
    if github_pat:
        url = f"https://{github_pat}@github.com/ayushrathore1/PrimeVector---SIH.git"

    if os.path.isdir(REPO_DIR):
        print(f"  ℹ️  Repo already exists at {REPO_DIR}, pulling latest...")
        subprocess.run(["git", "checkout", branch], cwd=REPO_DIR, check=False)
        subprocess.run(["git", "pull"], cwd=REPO_DIR, check=False)
    else:
        subprocess.run(["git", "clone", "-b", branch, url, REPO_DIR], check=True)

    print(f"  ✅ Repository ready at {REPO_DIR} (branch: {branch})\n")


# ──────────────────────────────────────────────────────────────────────────
# STEP 3: Start the 3 ML microservices as background processes
# ──────────────────────────────────────────────────────────────────────────

# Service definitions: (name, app_dir, port, env_vars)
SERVICES = [
    {
        "name": "feature-extraction-service",
        "app_dir": f"{REPO_DIR}/services/feature-extraction-service/app",
        "port": 8001,
        "env": {},
    },
    {
        "name": "spoof-detection-service",
        "app_dir": f"{REPO_DIR}/services/spoof-detection-service/app",
        "port": 8002,
        "env": {"SPOOF_MODEL_REGISTRY_BACKEND": "deepfake"},
    },
    {
        "name": "enrollment-service",
        "app_dir": f"{REPO_DIR}/services/enrollment-service/app",
        "port": 8003,
        "env": {},
    },
]

_processes = []

def start_ml_services():
    """Start each ML service as a background uvicorn process."""
    print("=" * 70)
    print("  🚀 STEP 3: Starting ML microservices...")
    print("=" * 70)

    for svc in SERVICES:
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{svc['app_dir']}:{os.path.dirname(svc['app_dir'])}"
        env.update(svc["env"])

        # Optimize PyTorch memory usage
        env["OMP_NUM_THREADS"] = "1"
        env["MKL_NUM_THREADS"] = "1"
        env["TORCH_NUM_THREADS"] = "1"

        cmd = [
            sys.executable, "-m", "uvicorn",
            "main:app",
            "--host", "0.0.0.0",
            "--port", str(svc["port"]),
            "--workers", "1",
        ]

        log_file = open(f"/content/{svc['name']}.log", "w")
        proc = subprocess.Popen(
            cmd,
            cwd=svc["app_dir"],
            env=env,
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )
        _processes.append((svc["name"], proc, log_file))
        print(f"  ▶ {svc['name']:30s} → port {svc['port']} (PID {proc.pid})")

    print("\n  ⏳ Waiting for ML models & PyTorch to initialize...")
    import urllib.request
    all_ok = True

    for svc in SERVICES:
        url = f"http://localhost:{svc['port']}/healthz"
        svc_healthy = False
        for attempt in range(12):  # Poll up to 30s (12 x 2.5s)
            try:
                resp = urllib.request.urlopen(url, timeout=3)
                if resp.status == 200:
                    svc_healthy = True
                    break
            except Exception:
                time.sleep(2.5)

        if svc_healthy:
            print(f"  {svc['name']:30s} → ✅ HEALTHY")
        else:
            print(f"  {svc['name']:30s} → ❌ FAILED (timed out loading model)")
            all_ok = False

    if not all_ok:
        print("\n  ⚠️  Some services failed to start. Check logs in /content/*.log")
    else:
        print("\n  ✅ All 3 ML services are running!\n")

    return all_ok


# ──────────────────────────────────────────────────────────────────────────
# STEP 4: Create reverse proxy (routes all 3 services through 1 port)
# ──────────────────────────────────────────────────────────────────────────

PROXY_PORT = 9090

PROXY_CODE = '''
"""
Reverse proxy — routes requests from 1 ngrok tunnel to 3 ML services.

Routes:
  /feat/...    → http://localhost:8001/...  (feature-extraction-service)
  /spoof/...   → http://localhost:8002/...  (spoof-detection-service)
  /enroll/...  → http://localhost:8003/...  (enrollment-service)
  /healthz     → combined health status of all 3 services
"""
import httpx
from fastapi import FastAPI, Request, Response

app = FastAPI(title="PrimeVector Colab Reverse Proxy")

client = None

@app.on_event("startup")
async def startup_event():
    global client
    client = httpx.AsyncClient(timeout=30.0, limits=httpx.Limits(max_keepalive_connections=20, max_connections=50))

@app.on_event("shutdown")
async def shutdown_event():
    global client
    if client:
        await client.aclose()

ROUTES = {
    "/feat": "http://localhost:8001",
    "/spoof": "http://localhost:8002",
    "/enroll": "http://localhost:8003",
}

@app.get("/healthz")
async def healthz():
    """Combined health check for all 3 ML services."""
    results = {}
    cli = client or httpx.AsyncClient(timeout=5.0)
    for prefix, base_url in ROUTES.items():
        try:
            resp = await cli.get(f"{base_url}/healthz")
            results[prefix] = {"status": "ok", "code": resp.status_code}
        except Exception as e:
            results[prefix] = {"status": "error", "detail": str(e)}
    all_ok = all(r["status"] == "ok" for r in results.values())
    return {"status": "ok" if all_ok else "degraded", "services": results}


@app.api_route("/{prefix}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy(prefix: str, path: str, request: Request):
    """Route requests to the appropriate ML service."""
    route_key = f"/{prefix}"
    if route_key not in ROUTES:
        return Response(
            content=f'{{"error": "Unknown route prefix: {prefix}. Use feat, spoof, or enroll."}}',
            status_code=404,
            media_type="application/json",
        )

    target_url = f"{ROUTES[route_key]}/{path}"

    # Forward the request
    body = await request.body()
    headers = dict(request.headers)
    headers.pop("host", None)

    cli = client or httpx.AsyncClient(timeout=30.0)
    try:
        resp = await cli.request(
            method=request.method,
            url=target_url,
            content=body,
            headers=headers,
        )
        return Response(
            content=resp.content,
            status_code=resp.status_code,
            media_type=resp.headers.get("content-type", "application/json"),
        )
    except httpx.TimeoutException:
        return Response(
            content='{"error": "Upstream service timeout"}',
            status_code=504,
            media_type="application/json",
        )
    except Exception as e:
        return Response(
            content=f'{{"error": "Proxy error: {str(e)}"}}',
            status_code=502,
            media_type="application/json",
        )
'''


def start_reverse_proxy():
    """Write and start the reverse proxy."""
    print("=" * 70)
    print("  🔀 STEP 4: Starting reverse proxy...")
    print("=" * 70)

    proxy_file = "/content/colab_proxy.py"
    with open(proxy_file, "w") as f:
        f.write(PROXY_CODE)

    env = os.environ.copy()
    cmd = [
        sys.executable, "-m", "uvicorn",
        "colab_proxy:app",
        "--host", "0.0.0.0",
        "--port", str(PROXY_PORT),
        "--workers", "1",
    ]

    log_file = open("/content/proxy.log", "w")
    proc = subprocess.Popen(
        cmd,
        cwd="/content",
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
    )
    _processes.append(("reverse-proxy", proc, log_file))
    time.sleep(3)

    print(f"  ✅ Reverse proxy running on port {PROXY_PORT}\n")
    return proc


# ──────────────────────────────────────────────────────────────────────────
# STEP 5: Open ngrok tunnel (free tier — 1 tunnel)
# ──────────────────────────────────────────────────────────────────────────

def start_ngrok_tunnel(auth_token=None):
    """Open an ngrok tunnel to the reverse proxy port."""
    print("=" * 70)
    print("  🌐 STEP 5: Opening ngrok tunnel...")
    print("=" * 70)

    from pyngrok import ngrok, conf

    if auth_token:
        ngrok.set_auth_token(auth_token)
        print("  ✅ ngrok auth token set.")
    else:
        # Try to read from environment
        token = os.environ.get("NGROK_AUTH_TOKEN", "")
        if token:
            ngrok.set_auth_token(token)
            print("  ✅ ngrok auth token loaded from environment.")
        else:
            print("  ⚠️  No ngrok auth token found. Tunnel may be limited.")
            print("     Get a free token at: https://dashboard.ngrok.com/get-started/your-authtoken")
            print("     Then re-run with: main(ngrok_auth_token='your_token_here')")

    # Open the tunnel
    tunnel = ngrok.connect(PROXY_PORT, "http")
    public_url = tunnel.public_url

    print(f"\n  {'=' * 60}")
    print(f"  🎉 NGROK TUNNEL IS LIVE!")
    print(f"  {'=' * 60}")
    print(f"  ")
    print(f"  Public URL: {public_url}")
    print(f"  ")
    print(f"  ┌──────────────────────────────────────────────────────┐")
    print(f"  │  COPY THIS INTO YOUR LOCAL .env FILE:               │")
    print(f"  │                                                      │")
    print(f"  │  COLAB_TUNNEL_URL={public_url}")
    print(f"  │                                                      │")
    print(f"  │  Then run: python run_local_lightweight.py           │")
    print(f"  └──────────────────────────────────────────────────────┘")
    print(f"  ")
    print(f"  Route map:")
    print(f"    {public_url}/feat/v1/extract     → Feature Extraction")
    print(f"    {public_url}/spoof/v1/detect     → Spoof Detection")
    print(f"    {public_url}/enroll/v1/tenants/  → Enrollment Service")
    print(f"    {public_url}/healthz             → Combined Health Check")
    print(f"  ")
    print(f"  ⚠️  Keep this Colab tab open! Closing it stops the tunnel.")
    print(f"  {'=' * 60}\n")

    return public_url


# ──────────────────────────────────────────────────────────────────────────
# Cleanup
# ──────────────────────────────────────────────────────────────────────────

def cleanup():
    """Kill all background processes."""
    print("\n  🛑 Shutting down all services...")
    for name, proc, log in _processes:
        try:
            proc.terminate()
            proc.wait(timeout=5)
            log.close()
            print(f"    ✅ {name} stopped.")
        except Exception:
            proc.kill()
            log.close()
            print(f"    ⚠️  {name} force-killed.")

    try:
        from pyngrok import ngrok
        ngrok.kill()
        print("    ✅ ngrok tunnel closed.")
    except Exception:
        pass


# ──────────────────────────────────────────────────────────────────────────
# Main entry point
# ──────────────────────────────────────────────────────────────────────────

def main(ngrok_auth_token=None, github_pat=None, branch="local-model-integration"):
    """
    Run everything. Call this from a Colab cell:

        # Option A: Without auth token (limited tunnel duration)
        main()

        # Option B: With auth token & private repo PAT
        main(ngrok_auth_token="your_ngrok_token", github_pat="ghp_xxxx", branch="local-model-integration")
    """
    print()
    print("  ╔══════════════════════════════════════════════════════════════╗")
    print("  ║   🛡️  SATYA PRIMEVECTOR — COLAB ML SERVICES LAUNCHER  🛡️   ║")
    print("  ║                                                              ║")
    print("  ║   Offloading heavy ML services to Google Colab's free        ║")
    print("  ║   12 GB RAM runtime so your 8 GB PC can breathe.            ║")
    print("  ╚══════════════════════════════════════════════════════════════╝")
    print()

    # Step 1: Install
    install_dependencies()

    # Step 2: Clone repo
    clone_repo(github_pat=github_pat, branch=branch)

    # Step 3: Start ML services
    start_ml_services()

    # Step 4: Start reverse proxy
    start_reverse_proxy()

    # Step 5: Open ngrok tunnel
    public_url = start_ngrok_tunnel(auth_token=ngrok_auth_token)

    # Keep alive
    print("  💡 This cell will keep running. Don't close this tab!")
    print("     Press the ⏹️ stop button or call cleanup() to shut down.\n")

    return public_url


# ──────────────────────────────────────────────────────────────────────────
# Auto-run when pasted into a Colab cell
# ──────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    main()
