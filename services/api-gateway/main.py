"""
PrimeVector API Gateway — Public-facing REST API for Dhwani 2 voice
deepfake detection.

Provides:
  - POST /v1/detect          — Single audio deepfake detection
  - POST /v1/detect/batch    — Batch detection (Pro+ tier)
  - GET  /v1/health          — Public health check
  - GET  /v1/keys            — List API keys (authenticated)
  - POST /v1/keys            — Create API key (authenticated)
  - DELETE /v1/keys/{key_id} — Revoke API key (authenticated)
  - GET  /v1/usage           — Current usage stats
  - GET  /v1/usage/history   — Historical usage
  - GET  /v1/usage/detections — Recent detection log

All detection endpoints forward to the spoof-detection-service
internally, add metering, and return a simplified response.
"""
from __future__ import annotations

import logging
import os
import secrets
import time
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta

import httpx
from fastapi import Depends, FastAPI, File, Header, HTTPException, Query, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

import auth
import metering
import storage
from models import (
    ApiKeyCreateRequest,
    ApiKeyListResponse,
    ApiKeyResponse,
    BatchDetectRequest,
    BatchDetectResponse,
    DetectRequest,
    DetectResponse,
    DetectionLogEntry,
    HealthResponse,
    RecentDetectionsResponse,
    Tier,
    UsageHistoryEntry,
    UsageHistoryResponse,
    UsageResponse,
    Verdict,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("primevector-gateway")

# ── Configuration ──────────────────────────────────────────

SPOOF_SERVICE_URL = os.environ.get(
    "SPOOF_SERVICE_URL", "http://localhost:8002"
)
STARTUP_TIME = time.time()


# ── Lifespan ───────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and seed demo data on startup."""
    storage.init_db()
    storage.seed_demo_data()
    logger.info(
        "PrimeVector API Gateway started. "
        "Spoof service: %s", SPOOF_SERVICE_URL
    )
    yield
    logger.info("PrimeVector API Gateway shutting down.")


# ── FastAPI App ────────────────────────────────────────────

app = FastAPI(
    title="PrimeVector API",
    version="1.0.0",
    description=(
        "Voice deepfake detection API powered by Dhwani 2. "
        "Detect AI-generated, cloned, and manipulated speech in real-time."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Dependency: Auth ───────────────────────────────────────

async def get_key_info(x_api_key: str = Header(default=None)):
    """Extract and validate API key from header."""
    if x_api_key is None:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "missing_api_key",
                "message": "X-API-Key header is required.",
            },
        )
    key_info = storage.validate_api_key(x_api_key)
    if key_info is None:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "invalid_api_key",
                "message": "Invalid or revoked API key.",
            },
        )
    return key_info


# ── Internal: Forward to spoof-detection-service ───────────

async def _detect_audio(audio_pcm_base64: str, sample_rate: int = 16000) -> dict:
    """Forward audio to the spoof-detection-service for inference."""
    payload = {
        "call_session_id": f"gw-{secrets.token_hex(8)}",
        "tenant_id": "api-gateway",
        "audio_features": [],
        "audio_pcm_base64": audio_pcm_base64,
        "sample_rate": sample_rate,
        "feature_type": "log_mel",
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{SPOOF_SERVICE_URL}/v1/detect",
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()


def _score_to_verdict(score: float, threshold: float = 0.5) -> Verdict:
    """Convert spoof score to a verdict."""
    if score >= threshold + 0.15:
        return Verdict.FAKE
    elif score <= threshold - 0.15:
        return Verdict.REAL
    else:
        return Verdict.UNCERTAIN


# ── Routes: Detection ──────────────────────────────────────

@app.post("/v1/detect", response_model=DetectResponse)
async def detect(
    req: DetectRequest,
    key_info: dict = Depends(get_key_info),
):
    """
    Detect deepfake in audio.

    Accepts base64-encoded 16-bit PCM audio (16kHz mono).
    Returns a verdict (real/fake/uncertain) with confidence score.
    """
    metering.enforce_rate_limit(key_info)

    session_id = req.session_id or f"pv-{secrets.token_hex(8)}"
    start = time.time()

    try:
        result = await _detect_audio(req.audio_pcm_base64, req.sample_rate)
    except httpx.HTTPStatusError as e:
        logger.error("Spoof service error: %s", e)
        raise HTTPException(502, detail="Detection service unavailable")
    except Exception as e:
        logger.error("Detection failed: %s", e)
        raise HTTPException(502, detail="Detection service unavailable")

    latency_ms = round((time.time() - start) * 1000, 1)
    score = result.get("score", 0.5)
    confidence = result.get("confidence", 0.0)
    detail = result.get("detail", "")

    # Extract model info from detail string
    model_version = "unknown"
    model_arch = "unknown"
    if "model=" in detail:
        for part in detail.split(", "):
            if part.startswith("model="):
                model_version = part.split("=", 1)[1]
            elif part.startswith("architecture="):
                model_arch = part.split("=", 1)[1]

    verdict = _score_to_verdict(score)

    # Derive logit from score
    import math
    clamped = max(1e-6, min(1 - 1e-6, score))
    raw_logit = round(math.log(clamped / (1 - clamped)), 4)

    # Meter the detection
    metering.record_detection(
        key_id=key_info["key_id"],
        session_id=session_id,
        verdict=verdict.value,
        spoof_score=score,
        confidence=confidence,
        latency_ms=latency_ms,
    )

    return DetectResponse(
        session_id=session_id,
        verdict=verdict,
        spoof_score=round(score, 4),
        confidence=round(confidence, 4),
        raw_logit=raw_logit,
        threshold=0.5,
        latency_ms=latency_ms,
        model_version=model_version,
        model_architecture=model_arch,
        timestamp=datetime.utcnow().isoformat(),
    )


@app.post("/v1/detect/batch", response_model=BatchDetectResponse)
async def detect_batch(
    req: BatchDetectRequest,
    key_info: dict = Depends(get_key_info),
):
    """
    Batch detection (Pro tier and above).

    Submit up to 10 audio samples in a single request.
    """
    auth.check_tier_access(key_info, "pro")
    metering.enforce_rate_limit(key_info)

    start = time.time()
    results = []
    for item in req.items:
        # Reuse single detect logic
        item_start = time.time()
        session_id = item.session_id or f"pv-{secrets.token_hex(8)}"

        try:
            result = await _detect_audio(item.audio_pcm_base64, item.sample_rate)
        except Exception:
            results.append(DetectResponse(
                session_id=session_id,
                verdict=Verdict.UNCERTAIN,
                spoof_score=0.5,
                confidence=0.0,
                raw_logit=0.0,
                threshold=0.5,
                latency_ms=round((time.time() - item_start) * 1000, 1),
                model_version="error",
                model_architecture="error",
                timestamp=datetime.utcnow().isoformat(),
            ))
            continue

        item_latency = round((time.time() - item_start) * 1000, 1)
        score = result.get("score", 0.5)
        confidence = result.get("confidence", 0.0)
        verdict = _score_to_verdict(score)

        import math
        clamped = max(1e-6, min(1 - 1e-6, score))
        raw_logit = round(math.log(clamped / (1 - clamped)), 4)

        metering.record_detection(
            key_id=key_info["key_id"],
            session_id=session_id,
            verdict=verdict.value,
            spoof_score=score,
            confidence=confidence,
            latency_ms=item_latency,
        )

        results.append(DetectResponse(
            session_id=session_id,
            verdict=verdict,
            spoof_score=round(score, 4),
            confidence=round(confidence, 4),
            raw_logit=raw_logit,
            threshold=0.5,
            latency_ms=item_latency,
            model_version=result.get("detail", "").split("model=")[-1].split(",")[0] if "model=" in result.get("detail", "") else "unknown",
            model_architecture="DhwaniV2",
            timestamp=datetime.utcnow().isoformat(),
        ))

    total_latency = round((time.time() - start) * 1000, 1)
    return BatchDetectResponse(results=results, total_latency_ms=total_latency)


# ── Routes: Health ─────────────────────────────────────────

@app.get("/v1/health", response_model=HealthResponse)
async def health():
    """Public health check — no authentication required."""
    # Probe the downstream spoof-detection-service
    model_loaded = False
    model_version = "unavailable"
    model_arch = "unavailable"

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{SPOOF_SERVICE_URL}/healthz")
            if resp.status_code == 200:
                data = resp.json()
                model_loaded = data.get("model_registered", False)
                model_version = data.get("registry_backend", "unknown")
                model_arch = "DhwaniV2-ResNetSE-BiGRU-Attention"
    except Exception:
        pass

    return HealthResponse(
        status="ok" if model_loaded else "degraded",
        model_loaded=model_loaded,
        model_version=model_version,
        model_architecture=model_arch,
        uptime_seconds=round(time.time() - STARTUP_TIME, 1),
    )


# ── Routes: API Keys ──────────────────────────────────────

@app.get("/v1/keys", response_model=ApiKeyListResponse)
async def list_keys(key_info: dict = Depends(get_key_info)):
    """List all API keys for the authenticated organization."""
    keys = storage.list_api_keys(key_info["org_id"])
    return ApiKeyListResponse(
        keys=[
            ApiKeyResponse(
                key_id=k["key_id"],
                api_key=k["api_key"],
                name=k["name"],
                tier=Tier(k["tier"]),
                created_at=k["created_at"],
                is_active=bool(k["is_active"]),
                org_id=k["org_id"],
            )
            for k in keys
        ],
        total=len(keys),
    )


@app.post("/v1/keys", response_model=ApiKeyResponse, status_code=201)
async def create_key(
    req: ApiKeyCreateRequest,
    key_info: dict = Depends(get_key_info),
):
    """Create a new API key for the authenticated organization."""
    key_id, raw_key = storage.create_api_key(
        org_id=key_info["org_id"],
        name=req.name,
        tier=req.tier,
    )
    return ApiKeyResponse(
        key_id=key_id,
        api_key=raw_key,
        name=req.name,
        tier=req.tier,
        created_at=datetime.utcnow().isoformat(),
        is_active=True,
        org_id=key_info["org_id"],
    )


@app.delete("/v1/keys/{key_id}", status_code=204)
async def revoke_key(
    key_id: str,
    key_info: dict = Depends(get_key_info),
):
    """Revoke an API key."""
    success = storage.revoke_api_key(key_id, key_info["org_id"])
    if not success:
        raise HTTPException(404, detail="API key not found")


# ── Routes: Usage ──────────────────────────────────────────

@app.get("/v1/usage", response_model=UsageResponse)
async def get_usage(key_info: dict = Depends(get_key_info)):
    """Get current usage statistics for the authenticated API key."""
    usage = storage.get_usage(key_info["key_id"], key_info["tier"])
    return UsageResponse(**usage)


@app.get("/v1/usage/history", response_model=UsageHistoryResponse)
async def get_usage_history(
    start_date: str = Query(
        default=None,
        description="Start date (YYYY-MM-DD). Defaults to 30 days ago.",
    ),
    end_date: str = Query(
        default=None,
        description="End date (YYYY-MM-DD). Defaults to today.",
    ),
    key_info: dict = Depends(get_key_info),
):
    """Get historical usage data for a date range."""
    if end_date is None:
        end_date = date.today().isoformat()
    if start_date is None:
        start_date = (date.today() - timedelta(days=30)).isoformat()

    entries = storage.get_usage_history(
        key_info["key_id"], start_date, end_date
    )

    total = sum(e["detections"] for e in entries)
    return UsageHistoryResponse(
        entries=[UsageHistoryEntry(**e) for e in entries],
        total_detections=total,
        period_start=start_date,
        period_end=end_date,
    )


@app.get("/v1/usage/detections", response_model=RecentDetectionsResponse)
async def get_recent_detections(
    limit: int = Query(default=50, le=200),
    key_info: dict = Depends(get_key_info),
):
    """Get recent detection log entries."""
    detections = storage.get_recent_detections(key_info["key_id"], limit)
    return RecentDetectionsResponse(
        detections=[DetectionLogEntry(**d) for d in detections],
        total=len(detections),
    )


# ── Root redirect ──────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "name": "PrimeVector API",
        "version": "1.0.0",
        "description": "Voice deepfake detection powered by Dhwani 2",
        "docs": "/docs",
        "health": "/v1/health",
    }
