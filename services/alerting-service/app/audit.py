"""
Audit logging for the alerting service.

Every alert sent (or attempted) is written to the audit log with:
- channel
- recipient (hashed, never raw contact info — DESIGN.md §7, §4.8)
- delivery status

The AuditLogger wraps an AuditLog backend and handles the SHA-256
hashing of recipient identifiers before writing. Raw contact info
never reaches the audit store.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone

from interfaces import AuditLog
from models import AuditEntry, Alert, DeliveryResult


class AuditLogger:
    """
    Writes immutable audit entries for every alert delivery attempt.

    Handles recipient hashing (SHA-256) so the raw contact info never
    leaves this layer. The underlying AuditLog backend only ever sees
    the hashed value.
    """

    def __init__(self, audit_log: AuditLog) -> None:
        self._log = audit_log

    @staticmethod
    def hash_recipient(recipient: str) -> str:
        """
        SHA-256 hash of the raw recipient identifier.

        This is the only form of the recipient that is ever written to
        the audit log — raw contact info (phone numbers, email addresses)
        is NEVER persisted in the audit trail (DESIGN.md §7, §4.8).
        """
        return hashlib.sha256(recipient.encode("utf-8")).hexdigest()

    def record(self, alert: Alert, result: DeliveryResult) -> AuditEntry:
        """
        Write an audit entry for an alert delivery attempt.

        Called for both successful and failed deliveries — the audit
        trail must capture all attempts, not just successes.

        Parameters
        ----------
        alert : Alert
            The alert that was sent (or attempted).
        result : DeliveryResult
            The outcome of the delivery attempt.

        Returns
        -------
        AuditEntry
            The written audit entry (for test assertions).
        """
        entry = AuditEntry(
            entry_id=str(uuid.uuid4()),
            event_id=alert.event_id,
            call_session_id=alert.call_session_id,
            tenant_id=alert.tenant_id,
            channel=result.channel,
            recipient_hash=self.hash_recipient(alert.recipient),
            status=result.status.value,
            detail=result.detail,
            timestamp=datetime.now(timezone.utc),
        )
        self._log.write(entry)
        return entry

    def get_entries(self, tenant_id: str) -> list[AuditEntry]:
        """Retrieve audit entries for a tenant."""
        return self._log.get_entries(tenant_id)
