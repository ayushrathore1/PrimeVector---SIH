# ==========================================================================
#   SATYA PRIMEVECTOR — GOOGLE COLAB ML SERVICES LAUNCHER (SELF-CONTAINED)
# ==========================================================================

import subprocess
import sys
import os
import time

# 1. Install dependencies
print("=" * 70)
print("  📦 STEP 1: Installing dependencies...")
print("=" * 70)
packages = [
    "fastapi", "uvicorn[standard]", "pydantic", "pydantic-settings",
    "httpx", "numpy", "librosa", "resemblyzer",
    "opentelemetry-api", "opentelemetry-sdk", "pyngrok", "pytest", "hypothesis",
]
subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "torch", "--index-url", "https://download.pytorch.org/whl/cpu"])
subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", *packages])
print("  ✅ All dependencies installed.\n")

# 2. Clone repository (handles private repo authentication)
GITHUB_PAT = ""  # If your repo is private, paste your GitHub PAT here (e.g. "ghp_xxxx")
REPO_DIR = "/content/PrimeVector"

print("=" * 70)
print("  📁 STEP 2: Cloning repository...")
print("=" * 70)

if not os.path.isdir(REPO_DIR):
    raw_url = f"https://{GITHUB_PAT}@github.com/ayushrathore1/PrimeVector---SIH.git" if GITHUB_PAT else "https://github.com/ayushrathore1/PrimeVector---SIH.git"
    res = subprocess.run(["git", "clone", raw_url, REPO_DIR])
    if res.returncode != 0:
        print("\n  🔒 Repository is private. A GitHub Personal Access Token (PAT) is required.")
        print("     Get a free token (repo scope) at: https://github.com/settings/tokens\n")
        try:
            pat = input("  👉 Paste your GitHub PAT token: ").strip()
            if pat:
                pat_url = f"https://{pat}@github.com/ayushrathore1/PrimeVector---SIH.git"
                subprocess.run(["git", "clone", pat_url, REPO_DIR], check=True)
            else:
                print("  ❌ Cannot clone private repository without a PAT token.")
                sys.exit(1)
        except (KeyboardInterrupt, EOFError):
            sys.exit(1)
else:
    subprocess.run(["git", "pull"], cwd=REPO_DIR, check=False)

print(f"  ✅ Repository ready at {REPO_DIR}\n")

# 3. Start Heavy ML Services (Feature Extraction :8001 & Speaker Enrollment :8003)
print("=" * 70)
print("  🚀 STEP 3: Starting ML microservices...")
print("=" * 70)
_processes = []
SERVICES = [
    {"name": "feature-extraction-service", "app_dir": f"{REPO_DIR}/services/feature-extraction-service/app", "port": 8001},
    {"name": "enrollment-service", "app_dir": f"{REPO_DIR}/services/enrollment-service/app", "port": 8003},
]

for svc in SERVICES:
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{svc['app_dir']}:{os.path.dirname(svc['app_dir'])}"
    cmd = [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", str(svc["port"]), "--workers", "1"]
    log_file = open(f"/content/{svc['name']}.log", "w")
    proc = subprocess.Popen(cmd, cwd=svc["app_dir"], env=env, stdout=log_file, stderr=subprocess.STDOUT)
    _processes.append((svc["name"], proc))
    print(f"  ▶ Started {svc['name']:30s} → port {svc['port']} (PID {proc.pid})")

time.sleep(4)
print("  ✅ ML services initialized.\n")

# 4. Start Reverse Proxy & Ngrok Tunnel
PROXY_PORT = 9090
PROXY_CODE = '''
import httpx
from fastapi import FastAPI, Request, Response
app = FastAPI()
client = None

@app.on_event("startup")
async def startup():
    global client
    client = httpx.AsyncClient(timeout=30.0)

ROUTES = {"/feat": "http://localhost:8001", "/enroll": "http://localhost:8003"}

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.api_route("/{prefix}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy(prefix: str, path: str, request: Request):
    route_key = f"/{prefix}"
    if route_key not in ROUTES:
        return Response(content='{"error": "Unknown route"}', status_code=404)
    body = await request.body()
    headers = dict(request.headers)
    headers.pop("host", None)
    resp = await client.request(method=request.method, url=f"{ROUTES[route_key]}/{path}", content=body, headers=headers)
    return Response(content=resp.content, status_code=resp.status_code, media_type=resp.headers.get("content-type", "application/json"))
'''

with open("/content/colab_proxy.py", "w") as f:
    f.write(PROXY_CODE)

proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "colab_proxy:app", "--host", "0.0.0.0", "--port", str(PROXY_PORT)])
_processes.append(("proxy", proc))
time.sleep(3)

# 5. Open Ngrok Tunnel
from pyngrok import ngrok

# Paste your free token from https://dashboard.ngrok.com/get-started/your-authtoken
NGROK_AUTH_TOKEN = "YOUR_NGROK_TOKEN_HERE"

if NGROK_AUTH_TOKEN and NGROK_AUTH_TOKEN != "YOUR_NGROK_TOKEN_HERE":
    ngrok.set_auth_token(NGROK_AUTH_TOKEN)

tunnel = ngrok.connect(PROXY_PORT, "http")

print("\n" + "=" * 65)
print("  🎉 NGROK TUNNEL IS LIVE!")
print("=" * 65)
print(f"  Public URL: {tunnel.public_url}")
print("=" * 65)
print(f"\n  COPY THIS INTO YOUR LOCAL .env FILE OR TERMINAL PROMPT:")
print(f"  COLAB_TUNNEL_URL={tunnel.public_url}\n")
