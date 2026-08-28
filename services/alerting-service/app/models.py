"""
Data models for the alerting service.

Domain dataclasses (frozen, immutable) for internal use, and Pydantic
models for the API layer. This separation follows the same pattern as
enrollment-service/app/models.py.

Audit entries use SHA-256 hashed recipient identifiers, never raw
contact info — per DESIGN.md §7 and §4.8.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Domain dataclasses (internal, frozen/immutable)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PolicyDecisionEvent:
    """
    Input event from the policy-threshold-engine.

    event_id is globally unique and is the idempotency key — the same
    event_id delivered twice must not produce duplicate alerts.
    """
    event_id: str
    call_session_id: str
    tenant_id: str
    action: str             # e.g. "RECOMMEND_CALLBACK_VERIFICATION"
    risk_score: float
    explanation: str
    timestamp: datetime


@dataclass(frozen=True)
class Alert:
    """
    Internal representation of an alert to be sent via a specific channel.

    Created by the AlertEngine for each (event, channel) pair.
    """
    alert_id: str
    event_id: str
    call_session_id: str
    tenant_id: str
    action: str
    channel: str            # "ui_push" | "sms_email"
    recipient: str          # raw recipient identifier
    message_body: str
    created_at: datetime


class DeliveryStatus(str, Enum):
    """Delivery outcome for an alert send attempt."""
    DELIVERED = "delivered"
    FAILED = "failed"


@dataclass(frozen=True)
class DeliveryResult:
    """Outcome of a channel.send() call."""
    alert_id: str
    channel: str
    status: DeliveryStatus
    detail: str


@dataclass(frozen=True)
class AuditEntry:
    """
    Immutable audit record for an alert delivery attempt.

    recipient_hash is a SHA-256 hex digest of the raw recipient — raw
    contact info is NEVER written to the audit log (DESIGN.md §7, §4.8).
    """
    entry_id: str
    event_id: str
    call_session_id: str
    tenant_id: str
    channel: str
    recipient_hash: str     # SHA-256 of raw contact, NEVER raw
    status: str             # "delivered" | "failed"
    detail: str
    timestamp: datetime


# ---------------------------------------------------------------------------
# Pydantic API models (request/response shapes)
# ---------------------------------------------------------------------------

class PolicyDecisionEventIn(BaseModel):
    """API request body for manual event injection (POST /v1/events)."""
    event_id: str
    call_session_id: str
    tenant_id: str
    action: str
    risk_score: float
    explanation: str


class AlertOut(BaseModel):
    """Single alert in the UI push poll response."""
    alert_id: str
    event_id: str
    call_session_id: str
    tenant_id: str
    action: str
    message_body: str
    created_at: str


class AlertsResponse(BaseModel):
    """Response for GET /v1/tenants/{tenant_id}/alerts."""
    alerts: list[AlertOut]


class AuditEntryOut(BaseModel):
    """Single entry in the audit log response."""
    entry_id: str
    event_id: str
    call_session_id: str
    tenant_id: str
    channel: str
    recipient_hash: str
    status: str
    detail: str
    timestamp: str


class AuditLogResponse(BaseModel):
    """Response for GET /v1/tenants/{tenant_id}/audit."""
    entries: list[AuditEntryOut]


class EventAcceptedResponse(BaseModel):
    """Response for POST /v1/events."""
    event_id: str
    channels_dispatched: int
    message: str
