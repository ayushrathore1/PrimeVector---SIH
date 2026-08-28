"""
Privacy enforcement tests for the enrollment service.

DESIGN.md §7: raw audio is never written to disk or persisted centrally.

These tests enforce this structurally — by inspecting the data models
themselves, not just trusting the code path. If someone adds an 'audio'
or 'raw_audio' field to any persisted model, these tests break.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

import inspect
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from enrollment import (
    AuditLogEntry,
    CaptureSession,
    EnrollmentService,
    MIN_SESSIONS_REQUIRED,
    Voiceprint,
)
from interfaces import StubLivenessChecker, StubModelRegistry
from store import InMemoryVoiceprintStore


TENANT = "bank-privacy-test"
SUBJECT = "user-001"
ADMIN = "admin-privacy"
ADMIN_ROLE = "tenant_admin"
AUDIO = b"raw-audio-bytes-that-must-not-be-stored-anywhere"


def _day(offset: int) -> datetime:
    base = datetime(2026, 1, 10, 12, 0, 0, tzinfo=timezone.utc)
    return base + timedelta(days=offset)


# ---------------------------------------------------------------------------
# Structural assertion: CaptureSession has no audio field
# ---------------------------------------------------------------------------

def test_capture_session_has_no_audio_field():
    """
    DESIGN.md §7: the CaptureSession model must not have any field
    that could hold raw audio bytes.
    """
    field_names = {f.name for f in CaptureSession.__dataclass_fields__.values()}
    for name in field_names:
        assert "audio" not in name.lower(), (
            f"CaptureSession has a field '{name}' that looks like it could "
            f"hold audio data — DESIGN.md §7 forbids this."
        )


# ---------------------------------------------------------------------------
# Structural assertion: Voiceprint has no audio field
# ---------------------------------------------------------------------------

def test_voiceprint_has_no_audio_field():
    """
    DESIGN.md §7: the Voiceprint model must not have any field
    that could hold raw audio bytes.
    """
    field_names = {f.name for f in Voiceprint.__dataclass_fields__.values()}
    for name in field_names:
        assert "audio" not in name.lower(), (
            f"Voiceprint has a field '{name}' that looks like it could "
            f"hold audio data — DESIGN.md §7 forbids this."
        )


# ---------------------------------------------------------------------------
# Structural assertion: AuditLogEntry has no audio field
# ---------------------------------------------------------------------------

def test_audit_log_entry_has_no_audio_field():
    field_names = {f.name for f in AuditLogEntry.__dataclass_fields__.values()}
    for name in field_names:
        assert "audio" not in name.lower(), (
            f"AuditLogEntry has a field '{name}' that looks like it could "
            f"hold audio data — DESIGN.md §7 forbids this."
        )


# ---------------------------------------------------------------------------
# Deep inspection: after full enrollment, no stored record contains the
# original audio bytes or any bytes object > 1KB
# ---------------------------------------------------------------------------

def test_no_raw_audio_in_persisted_records():
    """
    After a full enrollment flow, inspect every object in the store.
    Assert that the original audio bytes do not appear anywhere, and
    that no bytes object larger than 1KB exists in any stored record.
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

    # Collect every stored object
    all_objects = []
    vp_stored = store.get_voiceprint(TENANT, SUBJECT)
    if vp_stored:
        all_objects.append(("Voiceprint", vp_stored))

    for session in store.get_sessions(TENANT, SUBJECT):
        all_objects.append(("CaptureSession", session))

    for entry in store.get_audit_log(TENANT, SUBJECT):
        all_objects.append(("AuditLogEntry", entry))

    # Deep-inspect every field of every stored object
    for obj_name, obj in all_objects:
        _assert_no_audio_in_object(obj_name, obj, AUDIO)


def _assert_no_audio_in_object(label: str, obj, original_audio: bytes,
                                depth: int = 0, max_depth: int = 5):
    """Recursively inspect obj for any raw audio content."""
    if depth > max_depth:
        return

    if isinstance(obj, bytes):
        assert obj != original_audio, (
            f"{label} contains the original audio bytes — "
            f"DESIGN.md §7 violation"
        )
        assert len(obj) < 1024, (
            f"{label} contains a bytes object of {len(obj)} bytes — "
            f"suspiciously large, possible raw audio retention "
            f"(DESIGN.md §7)"
        )
        return

    if isinstance(obj, str):
        return  # strings are fine

    if isinstance(obj, (int, float, bool, type(None))):
        return

    if isinstance(obj, (list, tuple)):
        for i, item in enumerate(obj):
            _assert_no_audio_in_object(f"{label}[{i}]", item,
                                       original_audio, depth + 1)
        return

    if isinstance(obj, dict):
        for k, v in obj.items():
            _assert_no_audio_in_object(f"{label}.{k}", v,
                                       original_audio, depth + 1)
        return

    # Dataclass or other object — inspect its __dict__
    if hasattr(obj, "__dict__"):
        for attr_name, attr_val in obj.__dict__.items():
            _assert_no_audio_in_object(f"{label}.{attr_name}", attr_val,
                                       original_audio, depth + 1)
