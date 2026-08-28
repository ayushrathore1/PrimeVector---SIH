"""
Channel implementations for the alerting service.

Two channels behind the common Channel interface:

1. UIPushChannel — stores alerts in an in-memory per-tenant list that
   the frontend can poll (GET /v1/tenants/{tenant_id}/alerts). A future
   iteration could upgrade this to SSE or WebSocket push.

2. StubSMSEmailChannel — logs what WOULD be sent rather than actually
   integrating an SMS/email provider. This is intentionally stubbed per
   the task spec — not a TODO, but a deliberate design choice for this
   pass. When a real provider is wired in, this class gets replaced;
   the Channel ABC ensures the swap is mechanical.

⚠️ FLAGGED FOR FUTURE WORK: once a real SMS provider is wired in,
channel-specific retry with exponential backoff and a dead-letter
mechanism will be needed. Not built now per the task spec — single
straightforward retry only (handled in engine.py, not here).
"""

from __future__ import annotations

import logging
import threading
from collections import defaultdict

from interfaces import Channel
from models import Alert, DeliveryResult, DeliveryStatus

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# UIPushChannel — in-memory, pollable by frontend
# ---------------------------------------------------------------------------

class UIPushChannel(Channel):
    """
    Stores alerts in an in-memory per-tenant list. The frontend polls
    GET /v1/tenants/{tenant_id}/alerts to retrieve pending alerts.

    Thread-safe: multiple concurrent event-processing threads can
    write alerts without data races.
    """

    def __init__(self) -> None:
        self._alerts: dict[str, list[Alert]] = defaultdict(list)
        self._lock = threading.Lock()

    @property
    def name(self) -> str:
        return "ui_push"

    def send(self, alert: Alert) -> DeliveryResult:
        with self._lock:
            self._alerts[alert.tenant_id].append(alert)
        return DeliveryResult(
            alert_id=alert.alert_id,
            channel=self.name,
            status=DeliveryStatus.DELIVERED,
            detail="alert queued for UI polling",
        )

    def get_alerts(self, tenant_id: str) -> list[Alert]:
        """Retrieve pending alerts for a tenant (used by the API endpoint)."""
        with self._lock:
            return list(self._alerts.get(tenant_id, []))

    def alert_count(self, tenant_id: str) -> int:
        """Test helper: number of alerts for a tenant."""
        with self._lock:
            return len(self._alerts.get(tenant_id, []))


# ---------------------------------------------------------------------------
# StubSMSEmailChannel — logs what would be sent, no real provider
# ---------------------------------------------------------------------------

class StubSMSEmailChannel(Channel):
    """
    Stub SMS/email channel that logs what WOULD be sent rather than
    actually integrating a provider.

    This is intentionally stubbed — not a TODO, but a deliberate design
    choice for this pass. Do not wire a real SMS provider here; when
    one is needed, create a new class implementing Channel and swap it
    in via dependency injection.

    For testing: also records sent alerts in an in-memory list so tests
    can assert on what was "sent".
    """

    def __init__(self) -> None:
        self._sent: list[Alert] = []
        self._lock = threading.Lock()
        # Set to True to simulate a delivery failure (for retry testing)
        self._force_fail: bool = False
        self._fail_count: int = 0
        self._max_failures: int = 0

    @property
    def name(self) -> str:
        return "sms_email"

    def send(self, alert: Alert) -> DeliveryResult:
        # Simulate failure for testing retry logic
        if self._force_fail:
            with self._lock:
                if self._fail_count < self._max_failures:
                    self._fail_count += 1
                    logger.warning(
                        "StubSMSEmailChannel: simulated failure for "
                        "alert_id=%s (failure %d/%d)",
                        alert.alert_id, self._fail_count, self._max_failures,
                    )
                    return DeliveryResult(
                        alert_id=alert.alert_id,
                        channel=self.name,
                        status=DeliveryStatus.FAILED,
                        detail="stub: simulated delivery failure for testing",
                    )

        # Normal path: log what would be sent
        logger.info(
            "StubSMSEmailChannel: WOULD SEND alert to recipient=%s "
            "channel=sms_email action=%s call_session_id=%s tenant_id=%s "
            "message=%s",
            alert.recipient,
            alert.action,
            alert.call_session_id,
            alert.tenant_id,
            alert.message_body,
        )
        with self._lock:
            self._sent.append(alert)
        return DeliveryResult(
            alert_id=alert.alert_id,
            channel=self.name,
            status=DeliveryStatus.DELIVERED,
            detail="stub: logged (no real SMS/email provider wired)",
        )

    def get_sent(self) -> list[Alert]:
        """Test helper: return all alerts that were 'sent' (logged)."""
        with self._lock:
            return list(self._sent)

    def sent_count(self) -> int:
        """Test helper: number of alerts sent."""
        with self._lock:
            return len(self._sent)

    def set_failure_mode(self, max_failures: int) -> None:
        """
        Test helper: make the next `max_failures` send() calls fail,
        then succeed. Used to test the single-retry logic in engine.py.
        """
        self._force_fail = True
        self._max_failures = max_failures
        self._fail_count = 0
