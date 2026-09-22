#!/usr/bin/env python3
"""
=============================================================================
  SATYADH VANI 2 (PRIMEVECTOR) — PRODUCTION ENTRYPOINT & REVERSE PROXY
=============================================================================
  Universal cloud entrypoint for Docker environments (Render, Koyeb, HF, VPS).
  1. Boots internal microservices on loopback (127.0.0.1).
  2. Binds high-performance reverse proxy to 0.0.0.0:$PORT.
  3. Exposes:
     - /v1/*         -> API Gateway (:8090)
     - /api/8090/*   -> API Gateway (:8090)
     - /api/8002/*   -> SatyaDhVani Neural Spoof Detector (:8002)
     - /api/8085/*   -> Pipeline Orchestrator (:8085)
     - /api/8080/*   -> Pipeline Orchestrator (:8085)
     - /api/8000/*   -> Risk Fusion Engine (:8000)
     - /api/8001/*   -> Feature Extraction Service (:8001)
     - /api/8003/*   -> Speaker Enrollment Service (:8003)
     - /api/8004/*   -> Policy Threshold Engine (:8004)
     - /api/8005/*   -> Alerting Service (:8005)
     - /healthz      -> Cluster Health Aggregator
     - /*            -> Built React 19 Frontend (SPA fallback)
  4. Injects universal CORS headers for external web clients (e.g. Vercel).
  5. Graceful SIGINT/SIGTERM multi-process cleanup.
=============================================================================
"""

import asyncio
import logging
import os
import signal
import subprocess
import sys
import time
from contextlib import asynccontextmanager
from typing import Dict, List, Optional

import httpx
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("primevector-entrypoint")

PORT = int(os.environ.get("PORT", "7860"))
HOST = "0.0.0.0"
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WEBSITE_DIST = os.path.join(BASE_DIR, "website", "dist")
FRONTEND_DIST = os.path.join(BASE_DIR, "frontend", "dist")

STATIC_DIR = (
    WEBSITE_DIST
    if os.path.isfile(os.path.join(WEBSITE_DIST, "index.html"))
    else (
        FRONTEND_DIST
        if os.path.isfile(os.path.join(FRONTEND_DIST, "index.html"))
        else BASE_DIR
    )
)

# ── Microservices Definition ────────────────────────────────

MICROSERVICES = [
    {
        "name": "risk-fusion-engine",
        "app_dir": os.path.join(BASE_DIR, "services", "risk-fusion-engine", "app"),
        "port": 8000,
        "module": "main:app",
        "env": {},
    },
    {
        "name": "feature-extraction-service",
        "app_dir": os.path.join(BASE_DIR, "services", "feature-extraction-service", "app"),
        "port": 8001,
        "module": "main:app",
        "env": {},
    },
    {
        "name": "spoof-detection-service",
        "app_dir": os.path.join(BASE_DIR, "services", "spoof-detection-service", "app"),
        "port": 8002,
        "module": "main:app",
        "env": {
            "SPOOF_MODEL_REGISTRY_BACKEND": "satyadhvani",
            "KMP_DUPLICATE_LIB_OK": "TRUE",
        },
    },
    {
        "name": "enrollment-service",
        "app_dir": os.path.join(BASE_DIR, "services", "enrollment-service", "app"),
        "port": 8003,
        "module": "main:app",
        "env": {},
    },
    {
        "name": "policy-threshold-engine",
        "app_dir": os.path.join(BASE_DIR, "services", "policy-threshold-engine", "app"),
        "port": 8004,
        "module": "main:app",
        "env": {},
    },
    {
        "name": "alerting-service",
        "app_dir": os.path.join(BASE_DIR, "services", "alerting-service", "app"),
        "port": 8005,
        "module": "main:app",
        "env": {},
    },
    {
        "name": "api-gateway",
        "app_dir": os.path.join(BASE_DIR, "services", "api-gateway"),
        "port": 8090,
        "module": "main:app",
        "env": {
            "SPOOF_SERVICE_URL": "http://127.0.0.1:8002",
            "POLICY_ENGINE_URL": "http://127.0.0.1:8004",
        },
    },
    {
        "name": "orchestrator",
        "app_dir": os.path.join(BASE_DIR, "services", "orchestrator", "app"),
        "port": 8085,
        "module": "main:app",
        "env": {
            "FEATURE_EXTRACTION_URL": "http://127.0.0.1:8001",
            "SPOOF_DETECTION_URL": "http://127.0.0.1:8002",
            "ENROLLMENT_URL": "http://127.0.0.1:8003",
            "RISK_FUSION_URL": "http://127.0.0.1:8000",
            "POLICY_ENGINE_URL": "http://127.0.0.1:8004",
            "ALERTING_URL": "http://127.0.0.1:8005",
        },
    },
]

CHILD_PROCESSES: List[subprocess.Popen] = []
HTTP_CLIENT: Optional[httpx.AsyncClient] = None


def spawn_microservices():
    """Start all microservices as background uvicorn processes on loopback."""
    logger.info("Spawning PrimeVector microservices cluster...")
    for svc in MICROSERVICES:
        name = svc["name"]
        port = svc["port"]
        app_dir = svc["app_dir"]

        if not os.path.isdir(app_dir):
            logger.warning("Directory %s not found. Skipping %s.", app_dir, name)
            continue

        env = os.environ.copy()
        env["PYTHONPATH"] = f"{app_dir}{os.pathsep}{os.path.dirname(app_dir)}"
        env["OMP_NUM_THREADS"] = "1"
        env["TORCH_NUM_THREADS"] = "2"
        env.update(svc.get("env", {}))

        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            svc["module"],
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--workers",
            "1",
            "--log-level",
            "warning",
        ]

        try:
            proc = subprocess.Popen(cmd, cwd=app_dir, env=env)
            CHILD_PROCESSES.append(proc)
            logger.info("Launched %s (port :%d, PID %d)", name, port, proc.pid)
        except Exception as e:
            logger.error("Failed to launch %s: %s", name, e)


def stop_microservices():
    """Terminate all background processes."""
    logger.info("Stopping microservices...")
    for proc in CHILD_PROCESSES:
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
    logger.info("All microservices stopped.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global HTTP_CLIENT
    HTTP_CLIENT = httpx.AsyncClient(
        timeout=30.0,
        limits=httpx.Limits(max_keepalive_connections=50, max_connections=100),
    )
    spawn_microservices()
    yield
    if HTTP_CLIENT:
        await HTTP_CLIENT.aclose()
    stop_microservices()


app = FastAPI(
    title="SatyaDhVani 2 Production Gateway",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Reverse Proxy Engine ────────────────────────────────────

PORT_MAP = {
    8000: 8000,
    8001: 8001,
    8002: 8002,
    8003: 8003,
    8004: 8004,
    8005: 8005,
    8080: 8085,  # 8080 remapped to 8085 internally
    8085: 8085,
    8090: 8090,
}


async def forward_request(target_url: str, request: Request) -> Response:
    """Forward incoming request to local upstream microservice."""
    client = HTTP_CLIENT or httpx.AsyncClient(timeout=30.0)
    body = await request.body()
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None)

    try:
        upstream_resp = await client.request(
            method=request.method,
            url=target_url,
            content=body,
            headers=headers,
            params=request.query_params,
        )

        response_headers = dict(upstream_resp.headers)
        response_headers.pop("content-encoding", None)
        response_headers.pop("content-length", None)
        response_headers["access-control-allow-origin"] = "*"
        response_headers["access-control-allow-methods"] = "*"
        response_headers["access-control-allow-headers"] = "*"

        return Response(
            content=upstream_resp.content,
            status_code=upstream_resp.status_code,
            headers=response_headers,
            media_type=upstream_resp.headers.get("content-type"),
        )
    except httpx.ConnectError:
        return JSONResponse(
            status_code=503,
            content={"error": "Upstream microservice is booting or unavailable."},
        )
    except httpx.TimeoutException:
        return JSONResponse(
            status_code=504,
            content={"error": "Upstream microservice timed out."},
        )
    except Exception as exc:
        return JSONResponse(
            status_code=502,
            content={"error": f"Gateway proxy error: {str(exc)}"},
        )


@app.api_route("/v1/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"])
async def route_v1_to_api_gateway(path: str, request: Request):
    """Direct alias for API Gateway endpoints."""
    target_url = f"http://127.0.0.1:8090/v1/{path}"
    return await forward_request(target_url, request)


@app.api_route("/api/{port:int}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"])
async def route_api_by_port(port: int, path: str, request: Request):
    """Route by port convention /api/<port>/<path>."""
    mapped_port = PORT_MAP.get(port, port)
    target_url = f"http://127.0.0.1:{mapped_port}/{path.lstrip('/')}"
    return await forward_request(target_url, request)


@app.get("/healthz")
async def aggregated_health():
    """Aggregated health check querying all microservices."""
    client = HTTP_CLIENT or httpx.AsyncClient(timeout=3.0)
    health_results = {}

    for svc in MICROSERVICES:
        port = svc["port"]
        name = svc["name"]
        path = "/v1/health" if port == 8090 else "/healthz"
        url = f"http://127.0.0.1:{port}{path}"
        try:
            resp = await client.get(url, timeout=1.5)
            health_results[name] = "online" if resp.status_code == 200 else f"HTTP {resp.status_code}"
        except Exception:
            health_results[name] = "booting / unreachable"

    all_online = any(status == "online" for status in health_results.values())
    return {
        "status": "healthy" if all_online else "degraded",
        "gateway_port": PORT,
        "services": health_results,
    }


# ── Static Frontend & SPA Fallback ──────────────────────────

if os.path.isdir(STATIC_DIR) and os.path.isfile(os.path.join(STATIC_DIR, "index.html")):
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")


@app.get("/{full_path:path}")
async def serve_spa_frontend(full_path: str):
    """Serve static web assets with client-side SPA routing fallback."""
    candidate = os.path.join(STATIC_DIR, full_path)
    if full_path and os.path.isfile(candidate):
        return FileResponse(candidate)

    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.isfile(index_file):
        return FileResponse(index_file)

    dashboard_file = os.path.join(BASE_DIR, "test-dashboard.html")
    if os.path.isfile(dashboard_file):
        return FileResponse(dashboard_file)

    return JSONResponse(
        content={
            "platform": "SatyaDhVani 2 (PrimeVector)",
            "message": "Backend API is online. Frontend static build not found.",
            "api_endpoints": "/v1/detect, /v1/health, /healthz",
        }
    )


def main():
    def handle_signal(sig, frame):
        stop_microservices()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    logger.info("Starting SatyaDhVani 2 Production Gateway on %s:%d", HOST, PORT)
    uvicorn.run(app, host=HOST, port=PORT, access_log=False)


if __name__ == "__main__":
    main()
