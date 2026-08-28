"""
In-memory voiceprint store for the enrollment service.

This is a pluggable storage backend — production would use a database
with encryption at rest (DESIGN.md §4.9) and regional replication.

The InMemoryVoiceprintStore is keyed by (tenant_id, subject_id) since
enrollment is tenant-scoped (DESIGN.md §4.1) and each subject has at
most one active voiceprint at a time.
"""


class InMemoryVoiceprintStore:
    """
    Dict-backed in-memory store. Thread-safety is not addressed here
    (single-worker dev mode); a production store would use proper
    transactional semantics.
    """

    def __init__(self):
        self._voiceprints = {}   # (tenant_id, subject_id) -> Voiceprint
        self._sessions = {}      # (tenant_id, subject_id) -> [CaptureSession]
        self._audit_log = {}     # (tenant_id, subject_id) -> [AuditLogEntry]

    # -- Voiceprint --------------------------------------------------

    def save_voiceprint(self, vp) -> None:
        self._voiceprints[(vp.tenant_id, vp.subject_id)] = vp

    def get_voiceprint(self, tenant_id: str, subject_id: str):
        return self._voiceprints.get((tenant_id, subject_id))

    # -- Capture sessions --------------------------------------------

    def save_session(self, session) -> None:
        key = (session.tenant_id, session.subject_id)
        if key not in self._sessions:
            self._sessions[key] = []
        self._sessions[key].append(session)

    def get_sessions(self, tenant_id: str, subject_id: str) -> list:
        return list(self._sessions.get((tenant_id, subject_id), []))

    # -- Audit log ---------------------------------------------------

    def save_audit_entry(self, entry) -> None:
        key = (entry.tenant_id, entry.subject_id)
        if key not in self._audit_log:
            self._audit_log[key] = []
        self._audit_log[key].append(entry)

    def get_audit_log(self, tenant_id: str, subject_id: str) -> list:
        return list(self._audit_log.get((tenant_id, subject_id), []))
