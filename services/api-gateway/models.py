"""
Pydantic schemas for the PrimeVector API Gateway.

All request/response types for the public-facing deepfake
detection API, API key management, and usage tracking.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ── Enums ──────────────────────────────────────────────────

class Tier(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class Verdict(str, Enum):
    REAL = "real"
    FAKE = "fake"
    UNCERTAIN = "uncertain"


# ── Detection ──────────────────────────────────────────────

class DetectRequest(BaseModel):
    """JSON body for base64 audio detection."""
    audio_pcm_base64: str = Field(
        ..., description="Base64-encoded 16-bit PCM audio (16kHz mono)"
    )
    sample_rate: int = Field(default=16000)
    session_id: Optional[str] = Field(
        default=None,
        description="Optional caller-provided session ID for tracking",
    )


class DetectResponse(BaseModel):
    """Result of a single deepfake detection."""
    session_id: str
    verdict: Verdict
    spoof_score: float = Field(
        ge=0.0, le=1.0,
        description="0.0 = real, 1.0 = fake",
    )
    confidence: float = Field(ge=0.0, le=1.0)
    raw_logit: float
    threshold: float = 0.5
    latency_ms: float
    model_version: str
    model_architecture: str
    timestamp: str


class BatchDetectRequest(BaseModel):
    """Batch detection request (Pro+ tier)."""
    items: list[DetectRequest] = Field(
        ..., max_length=10,
        description="Up to 10 audio samples per batch request",
    )


class BatchDetectResponse(BaseModel):
    """Batch detection results."""
    results: list[DetectResponse]
    total_latency_ms: float


# ── API Keys ───────────────────────────────────────────────

class ApiKeyCreateRequest(BaseModel):
    """Request to create a new API key."""
    name: str = Field(
        ..., min_length=1, max_length=100,
        description="Human-readable name for this key",
    )
    tier: Tier = Field(default=Tier.FREE)


class ApiKeyResponse(BaseModel):
    """API key details."""
    key_id: str
    api_key: str  # Only shown on creation; masked elsewhere
    name: str
    tier: Tier
    created_at: str
    is_active: bool
    org_id: str


class ApiKeyListResponse(BaseModel):
    """List of API keys for an organization."""
    keys: list[ApiKeyResponse]
    total: int


# ── Usage ──────────────────────────────────────────────────

class UsageResponse(BaseModel):
    """Current usage statistics for an API key."""
    api_key_id: str
    tier: Tier
    detections_today: int
    detections_this_month: int
    daily_limit: int
    monthly_limit: int
    remaining_today: int
    avg_latency_ms: float
    verdicts: dict[str, int] = Field(
        default_factory=dict,
        description="Breakdown: {'real': N, 'fake': N, 'uncertain': N}",
    )


class UsageHistoryEntry(BaseModel):
    """Single day's usage aggregate."""
    date: str
    detections: int
    real_count: int
    fake_count: int
    uncertain_count: int
    avg_latency_ms: float


class UsageHistoryResponse(BaseModel):
    """Historical usage data."""
    entries: list[UsageHistoryEntry]
    total_detections: int
    period_start: str
    period_end: str


class DetectionLogEntry(BaseModel):
    """Single detection log entry."""
    session_id: str
    timestamp: str
    verdict: Verdict
    spoof_score: float
    confidence: float
    latency_ms: float


class RecentDetectionsResponse(BaseModel):
    """Recent detection log."""
    detections: list[DetectionLogEntry]
    total: int


# ── Health ─────────────────────────────────────────────────

class HealthResponse(BaseModel):
    """Service health status."""
    status: str = "ok"
    model_loaded: bool
    model_version: str
    model_architecture: str
    uptime_seconds: float
