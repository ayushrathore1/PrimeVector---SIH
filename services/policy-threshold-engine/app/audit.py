"""
Audit log for the policy-threshold-engine.

REVIEW FLAG: This module is flagged for human review before merge.
This is the code path a bank's compliance team will ask to see
(DESIGN.md §4.8). Every policy configuration change — threshold edits,
auto_block toggling — must produce an immutable audit log entry with:
  - Actor identity (who made the change)
  - Old value
  - New value
  - Timestamp

Implementation note: This reference implementation uses an append-only
in-memory list. A production deployment would use an immutable event
store (e.g., append-only database table, event log) with the same
interface. The critical property is append-only: there is no delete or
update operation on audit entries.
"""

import threading
from datetime import datetime, timezone

from models import AuditLogEntry


class AuditLog:
    """
    Append-only audit log for policy configuration changes.

    Thread-safe. No delete or update operations exist by design —
    audit entries are immutable once written.
    """

    def __init__(self) -> None:
        self._entries: list[AuditLogEntry] = []
        self._lock = threading.Lock()

    def append(self, entry: AuditLogEntry) -> None:
        """
        Append an audit log entry. This is the only write operation.
        There is no delete or update — entries are immutable.
        """
        with self._lock:
            self._entries.append(entry)

    def get_entries(self, tenant_id: str | None = None) -> list[AuditLogEntry]:
        """
        Return audit entries, optionally filtered by tenant_id.

        Returns a copy to prevent external mutation of the log.
        """
        with self._lock:
            if tenant_id is None:
                return list(self._entries)
            return [e for e in self._entries if e.tenant_id == tenant_id]

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)
