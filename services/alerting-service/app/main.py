"""
Alerting service — thin FastAPI wrapper.

The wrapper (this file) is boilerplate and can be safely regenerated or
extended by an AI coding tool. The logic it wraps (engine.py) is the
core component — see docs/DESIGN.md section 6.

Endpoints:
- POST /v1/events       — manual event injection (testing/integration)
- GET  /v1/tenants/{tenant_id}/alerts — UI push poll
- GET  /v1/tenants/{tenant_id}/audit  — audit trail query
- GET  /healthz          — liveness check
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI

from dependencies import (
    POLICY_DECISIONS_TOPIC,
    get_audit_logger,
    get_engine,
    get_pubsub,
    get_ui_push_channel,
)
from engine import AlertEngine
from audit import AuditLogger
from channels import UIPushChannel
from models import (
    AlertOut,
    AlertsResponse,
    AuditEntryOut,
    AuditLogResponse,
    EventAcceptedResponse,
    PolicyDecisionEvent,
    PolicyDecisionEventIn,
)
from subscriber import InMemoryPubSub

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Background consumer loop
# ---------------------------------------------------------------------------

async def _consumer_loop(pubsub: InMemoryPubSub, engine: AlertEngine) -> None:
    """
    Background task that drains the Pub/Sub topic and processes events
    through the alert engine. Runs for the lifetime of the application.

    In production, this would be replaced by a real Pub/Sub pull
    subscriber with proper error handling and graceful shutdown.
    """
    pubsub.subscribe(POLICY_DECISIONS_TOPIC, engine.process_event)
    while True:
        try:
            pubsub.drain(POLICY_DECISIONS_TOPIC)
        except Exception:
            logger.exception("Error draining Pub/Sub topic")
        await asyncio.sleep(0.1)  # 100ms poll interval


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan: starts the background consumer loop on startup."""
    engine = get_engine()
    pubsub = get_pubsub()
    task = asyncio.create_task(_consumer_loop(pubsub, engine))
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="alerting-service",
    version="0.1.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.post("/v1/events", response_model=EventAcceptedResponse)
def ingest_event(
    req: PolicyDecisionEventIn,
    engine: AlertEngine = Depends(get_engine),
) -> EventAcceptedResponse:
    """
    Manual event injection endpoint for testing and integration.

    In production, events arrive via Pub/Sub (the background consumer
    loop). This endpoint exists so the service can be tested end-to-end
    without a Pub/Sub emulator.
    """
    event = PolicyDecisionEvent(
        event_id=req.event_id,
        call_session_id=req.call_session_id,
        tenant_id=req.tenant_id,
        action=req.action,
        risk_score=req.risk_score,
        explanation=req.explanation,
        timestamp=datetime.now(timezone.utc),
    )
    dispatched = engine.process_event(event)
    return EventAcceptedResponse(
        event_id=req.event_id,
        channels_dispatched=dispatched,
        message=f"Event processed, dispatched to {dispatched} channel(s)",
    )


@app.get(
    "/v1/tenants/{tenant_id}/alerts",
    response_model=AlertsResponse,
)
def get_alerts(
    tenant_id: str,
    ui_push: UIPushChannel = Depends(get_ui_push_channel),
) -> AlertsResponse:
    """
    UI push poll endpoint — returns pending alerts for the tenant's
    frontend to display. A future iteration could upgrade this to
    SSE or WebSocket push.
    """
    alerts = ui_push.get_alerts(tenant_id)
    return AlertsResponse(
        alerts=[
            AlertOut(
                alert_id=a.alert_id,
                event_id=a.event_id,
                call_session_id=a.call_session_id,
                tenant_id=a.tenant_id,
                action=a.action,
                message_body=a.message_body,
                created_at=a.created_at.isoformat(),
            )
            for a in alerts
        ]
    )


@app.get(
    "/v1/tenants/{tenant_id}/audit",
    response_model=AuditLogResponse,
)
def get_audit_log(
    tenant_id: str,
    audit_logger: AuditLogger = Depends(get_audit_logger),
) -> AuditLogResponse:
    """
    Audit trail query endpoint. Returns all audit entries for a tenant,
    including both successful and failed delivery attempts.

    Per DESIGN.md §4.8: the audit log contains channel, hashed recipient
    (never raw contact info), and delivery status.
    """
    entries = audit_logger.get_entries(tenant_id)
    return AuditLogResponse(
        entries=[
            AuditEntryOut(
                entry_id=e.entry_id,
                event_id=e.event_id,
                call_session_id=e.call_session_id,
                tenant_id=e.tenant_id,
                channel=e.channel,
                recipient_hash=e.recipient_hash,
                status=e.status,
                detail=e.detail,
                timestamp=e.timestamp.isoformat(),
            )
            for e in entries
        ]
    )


@app.get("/healthz")
def healthz():
    return {"status": "ok"}
