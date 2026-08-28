"""
No-raw-audio assertion tests for the enrollment service.

DESIGN.md §7: raw audio must NEVER be stored at any stage. Only
embedding vectors are persisted. This test file goes beyond structural
checks (test_privacy.py) and verifies the property end-to-end: after
a full enrollment flow, the original audio bytes must not exist in ANY
persisted record.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from enrollment import EnrollmentService, MIN_SESSIONS_REQUIRED
from interfaces import StubLivenessChecker, StubModelRegistry
from store import InMemoryVoiceprintStore


TENANT = "bank-noaudio-test"
SUBJECT = "user-noaudio"
ADMIN = "admin-noaudio"
ADMIN_ROLE = "tenant_admin"

# Large-ish audio payload to make detection easier
AUDIO = b"X" * 4096  # 4KB of audio data


def _day(offset: int) -> datetime:
    base = datetime(2026, 1, 10, 12, 0, 0, tzinfo=timezone.utc)
    return base + timedelta(days=offset)


def _find_bytes_in_object(obj, target: bytes, path: str = "",
                          visited: set = None, depth: int = 0) -> list:
    """Recursively search for target bytes in any reachable object."""
    if visited is None:
        visited = set()
    if depth > 10 or id(obj) in visited:
        return []
    visited.add(id(obj))

    findings = []

    if isinstance(obj, bytes):
        if obj == target:
            findings.append(f"{path}: exact match of original audio bytes")
        elif len(obj) > 1024:
            findings.append(
                f"{path}: suspicious bytes object ({len(obj)} bytes)"
            )
        return findings

    if isinstance(obj, (str, int, float, bool, type(None))):
        return []

    if isinstance(obj, (list, tuple)):
        for i, item in enumerate(obj):
            findings.extend(
                _find_bytes_in_object(item, target, f"{path}[{i}]",
                                      visited, depth + 1)
            )
        return findings

    if isinstance(obj, dict):
        for k, v in obj.items():
            findings.extend(
                _find_bytes_in_object(v, target, f"{path}.{k}",
                                      visited, depth + 1)
            )
        return findings

    if hasattr(obj, "__dict__"):
        for attr, val in obj.__dict__.items():
            findings.extend(
                _find_bytes_in_object(val, target, f"{path}.{attr}",
                                      visited, depth + 1)
            )
    return findings


def test_no_raw_audio_bytes_in_any_persisted_record():
    """
    DESIGN.md §7: after a complete enrollment, the original audio bytes
    must not exist in ANY stored object (voiceprint, sessions, audit log).
    """
    store = InMemoryVoiceprintStore()
    svc = EnrollmentService(
        store=store,
        liveness_checker=StubLivenessChecker(),
        model_registry=StubModelRegistry(),
    )

    vp, challenge = svc.start_enrollment(TENANT, SUBJECT, ADMIN, ADMIN_ROLE)
    for day_offset in range(MIN_SESSIONS_REQUIRED):
        with patch("enrollment.datetime") as mock_dt:
            mock_dt.now.return_value = _day(day_offset)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            vp, challenge = svc.submit_session(
                TENANT, SUBJECT, AUDIO, challenge or "dummy",
                ADMIN, ADMIN_ROLE,
            )

    # Inspect everything in the store
    findings = []

    # Check voiceprint
    vp_stored = store.get_voiceprint(TENANT, SUBJECT)
    if vp_stored:
        findings.extend(
            _find_bytes_in_object(vp_stored, AUDIO, "Voiceprint")
        )

    # Check sessions
    for i, session in enumerate(store.get_sessions(TENANT, SUBJECT)):
        findings.extend(
            _find_bytes_in_object(session, AUDIO, f"CaptureSession[{i}]")
        )

    # Check audit log
    for i, entry in enumerate(store.get_audit_log(TENANT, SUBJECT)):
        findings.extend(
            _find_bytes_in_object(entry, AUDIO, f"AuditLogEntry[{i}]")
        )

    assert len(findings) == 0, (
        f"DESIGN.md §7 VIOLATION: raw audio found in persisted records:\n"
        + "\n".join(f"  - {f}" for f in findings)
    )


def test_store_internal_dicts_contain_no_audio():
    """
    Belt-and-suspenders: inspect the store's internal dictionaries
    directly to catch any audio that might be stored under unexpected
    keys.
    """
    store = InMemoryVoiceprintStore()
    svc = EnrollmentService(
        store=store,
        liveness_checker=StubLivenessChecker(),
        model_registry=StubModelRegistry(),
    )

    vp, challenge = svc.start_enrollment(TENANT, SUBJECT, ADMIN, ADMIN_ROLE)
    for day_offset in range(MIN_SESSIONS_REQUIRED):
        with patch("enrollment.datetime") as mock_dt:
            mock_dt.now.return_value = _day(day_offset)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            vp, challenge = svc.submit_session(
                TENANT, SUBJECT, AUDIO, challenge or "dummy",
                ADMIN, ADMIN_ROLE,
            )

    # Scan all internal store state
    findings = _find_bytes_in_object(
        store.__dict__, AUDIO, "Store.__dict__"
    )

    assert len(findings) == 0, (
        f"DESIGN.md §7 VIOLATION: raw audio found in store internals:\n"
        + "\n".join(f"  - {f}" for f in findings)
    )
