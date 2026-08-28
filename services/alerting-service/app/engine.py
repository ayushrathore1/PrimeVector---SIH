"""
Alert engine — core idempotent dispatch orchestrator.

This is the central piece of the alerting service. It:
1. Receives a PolicyDecisionEvent
2. Checks the DeliveryStore for each channel to enforce idempotency
   (same event_id + channel → skip, no duplicate alert)
3. Dispatches to each registered Channel
4. Performs a single retry on failure (no backoff — see module note)
5. Records delivery in the DeliveryStore
6. Writes an AuditEntry for every attempt (success or failure)

Design notes:
- At-least-once delivery from the publisher is acceptable (DESIGN.md).
  Duplicates are suppressed HERE at the consumer, not at the publisher.
- Single retry only. No exponential backoff, no retry queue, no DLQ.
  This is adequate for the current stubbed channels. When a real SMS
  provider is wired in, channel-specific retry with backoff and a
  dead-letter mechanism will be needed — flagged, not built.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from audit import AuditLogger
from interfaces import Channel, DeliveryStore
from models import Alert, DeliveryStatus, PolicyDecisionEvent

logger = logging.getLogger(__name__)


class AlertEngine:
    """
    Idempotent alert dispatcher.

    Given a policy decision event, dispatches alerts to all registered
    channels exactly once per (event_id, channel) — regardless of how
    many times the event is delivered by the upstream publisher.
    """

    def __init__(
        self,
        channels: list[Channel],
        delivery_store: DeliveryStore,
        audit_logger: AuditLogger,
    ) -> None:
        self._channels = channels
        self._delivery_store = delivery_store
        self._audit_logger = audit_logger

    def process_event(self, event: PolicyDecisionEvent) -> int:
        """
        Process a policy decision event: dispatch to all channels with
        idempotency enforcement.

        Parameters
        ----------
        event : PolicyDecisionEvent
            The event from the policy-threshold-engine.

        Returns
        -------
        int
            Number of channels that were actually dispatched to (excludes
            channels skipped due to idempotency).
        """
        dispatched = 0

        for channel in self._channels:
            # ----- Idempotency gate -----
            if self._delivery_store.has_delivered(event.event_id, channel.name):
                logger.info(
                    "Skipping duplicate: event_id=%s already delivered "
                    "to channel=%s",
                    event.event_id, channel.name,
                )
                continue

            # Build the alert for this channel
            alert = Alert(
                alert_id=str(uuid.uuid4()),
                event_id=event.event_id,
                call_session_id=event.call_session_id,
                tenant_id=event.tenant_id,
                action=event.action,
                channel=channel.name,
                recipient=self._resolve_recipient(event, channel.name),
                message_body=self._build_message(event),
                created_at=datetime.now(timezone.utc),
            )

            # ----- Dispatch with single retry -----
            result = channel.send(alert)

            if result.status == DeliveryStatus.FAILED:
                # Single retry — no backoff, no retry queue.
                logger.warning(
                    "First attempt failed for event_id=%s channel=%s: %s. "
                    "Retrying once.",
                    event.event_id, channel.name, result.detail,
                )
                # Audit the failed first attempt
                self._audit_logger.record(alert, result)

                # Retry
                result = channel.send(alert)
                if result.status == DeliveryStatus.FAILED:
                    logger.error(
                        "Retry also failed for event_id=%s channel=%s: %s. "
                        "Giving up.",
                        event.event_id, channel.name, result.detail,
                    )

            # Audit the final result (success or second failure)
            self._audit_logger.record(alert, result)

            # Mark as delivered regardless of outcome — we've made our
            # best effort (1 attempt + 1 retry). Re-delivering on the
            # next duplicate event would not help and could cause noise.
            # If delivery guarantees need to be stronger, a DLQ + manual
            # re-drive is the right mechanism, not re-processing the
            # same event.
            self._delivery_store.mark_delivered(event.event_id, channel.name)
            dispatched += 1

        return dispatched

    @staticmethod
    def _resolve_recipient(
        event: PolicyDecisionEvent,
        channel_name: str,
    ) -> str:
        """
        Resolve the recipient for a given event and channel.

        In production, this would look up a tenant's notification
        preferences (e.g., which staff members get SMS vs. UI alerts).
        For now, we use a deterministic placeholder based on tenant_id
        and channel, which is sufficient for wiring and testing.
        """
        # Deterministic placeholder — real implementation would query
        # a tenant notification preferences store.
        return f"{channel_name}:{event.tenant_id}:staff"

    @staticmethod
    def _build_message(event: PolicyDecisionEvent) -> str:
        """
        Build a human-readable alert message from the policy decision.
        """
        return (
            f"[{event.action}] Risk alert for call {event.call_session_id} "
            f"(risk_score={event.risk_score:.2f}): {event.explanation}"
        )
