"""
Audit log tests for the alerting service.

Verifies:
- Every delivery attempt writes an audit entry
- recipient_hash is a SHA-256 hex digest, never raw contact info
- Failed deliveries are also audited
- Audit entries contain all required fields (DESIGN.md §4.8)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

import hashlib
import re
from datetime import datetime, timezone

from audit import AuditLogger
from channels import StubSMSEmailChannel, UIPushChannel
from engine import AlertEngine
from interfaces import InMemoryAuditLog, InMemoryDeliveryStore
from models import PolicyDecisionEvent


def _make_event(event_id: str = "evt-audit-test") -> PolicyDecisionEvent:
    return PolicyDecisionEvent(
        event_id=event_id,
        call_session_id="call-audit-001",
        tenant_id="tenant-bank-1",
        action="RECOMMEND_SUPERVISOR_ESCALATION",
        risk_score=0.92,
        explanation="voice mismatch + elevated context",
        timestamp=datetime.now(timezone.utc),
    )


def _make_engine():
    ui_push = UIPushChannel()
    sms_email = StubSMSEmailChannel()
    delivery_store = InMemoryDeliveryStore()
    audit_log = InMemoryAuditLog()
    audit_logger = AuditLogger(audit_log)
    engine = AlertEngine(
        channels=[ui_push, sms_email],
        delivery_store=delivery_store,
        audit_logger=audit_logger,
    )
    return engine, ui_push, sms_email, audit_log, audit_logger


# -------------------------------------------------------------------
# Audit completeness
# -------------------------------------------------------------------

def test_every_delivery_writes_audit_entry():
    """Every channel dispatch produces an audit entry."""
    engine, _, _, audit_log, _ = _make_engine()
    event = _make_event()

    engine.process_event(event)

    # 2 channels → 2 audit entries
    entries = audit_log.all_entries
    assert len(entries) == 2

    channels_in_log = {e.channel for e in entries}
    assert channels_in_log == {"ui_push", "sms_email"}


def test_audit_entries_contain_required_fields():
    """
    Per DESIGN.md §4.8: every audit entry must include channel,
    recipient (hashed), and delivery status.
    """
    engine, _, _, audit_log, _ = _make_engine()
    event = _make_event()
    engine.process_event(event)

    for entry in audit_log.all_entries:
        # All required fields are present and non-empty
        assert entry.entry_id
        assert entry.event_id == "evt-audit-test"
        assert entry.call_session_id == "call-audit-001"
        assert entry.tenant_id == "tenant-bank-1"
        assert entry.channel in ("ui_push", "sms_email")
        assert entry.recipient_hash  # non-empty
        assert entry.status in ("delivered", "failed")
        assert entry.detail
        assert entry.timestamp


# -------------------------------------------------------------------
# Recipient hashing
# -------------------------------------------------------------------

def test_recipient_hash_is_sha256_not_raw():
    """
    The audit log must contain a SHA-256 hash of the recipient, NEVER
    the raw contact info (DESIGN.md §7, §4.8).
    """
    engine, _, _, audit_log, _ = _make_engine()
    event = _make_event()
    engine.process_event(event)

    for entry in audit_log.all_entries:
        # SHA-256 hex digest is exactly 64 hex characters
        assert len(entry.recipient_hash) == 64
        assert re.fullmatch(r"[0-9a-f]{64}", entry.recipient_hash), (
            f"recipient_hash does not look like SHA-256: {entry.recipient_hash}"
        )

        # Must NOT contain raw identifiers
        assert "tenant-bank-1" not in entry.recipient_hash
        assert "staff" not in entry.recipient_hash
        assert "@" not in entry.recipient_hash
        assert "+" not in entry.recipient_hash


def test_recipient_hash_matches_sha256_of_raw():
    """Verify the hash is a correct SHA-256 of the raw recipient."""
    logger = AuditLogger(InMemoryAuditLog())

    raw = "sms_email:tenant-bank-1:staff"
    expected = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    actual = logger.hash_recipient(raw)

    assert actual == expected


def test_different_recipients_produce_different_hashes():
    """Sanity check: distinct recipients → distinct hashes."""
    logger = AuditLogger(InMemoryAuditLog())
    h1 = logger.hash_recipient("alice@example.com")
    h2 = logger.hash_recipient("bob@example.com")
    assert h1 != h2


# -------------------------------------------------------------------
# Failed deliveries are audited
# -------------------------------------------------------------------

def test_failed_delivery_is_audited():
    """
    A failed delivery attempt must also produce an audit entry with
    status='failed' — the audit trail captures ALL attempts, not just
    successes.
    """
    sms_email = StubSMSEmailChannel()
    sms_email.set_failure_mode(max_failures=999)  # always fail

    delivery_store = InMemoryDeliveryStore()
    audit_log = InMemoryAuditLog()
    audit_logger = AuditLogger(audit_log)

    engine = AlertEngine(
        channels=[sms_email],
        delivery_store=delivery_store,
        audit_logger=audit_logger,
    )

    event = _make_event("evt-fail-audit")
    engine.process_event(event)

    entries = audit_log.all_entries
    # Should have 2 entries: first attempt (failed) + retry (also failed)
    assert len(entries) == 2
    assert all(e.status == "failed" for e in entries)
    assert all(e.channel == "sms_email" for e in entries)


def test_successful_delivery_status_in_audit():
    """Successful deliveries are recorded with status='delivered'."""
    engine, _, _, audit_log, _ = _make_engine()
    event = _make_event("evt-success-audit")
    engine.process_event(event)

    delivered_entries = [e for e in audit_log.all_entries if e.status == "delivered"]
    assert len(delivered_entries) == 2  # both channels succeeded


# -------------------------------------------------------------------
# Audit entries are tenant-scoped
# -------------------------------------------------------------------

def test_audit_entries_are_tenant_scoped():
    """get_entries filters by tenant_id."""
    engine, _, _, _, audit_logger = _make_engine()

    event_a = PolicyDecisionEvent(
        event_id="evt-a",
        call_session_id="call-a",
        tenant_id="tenant-alpha",
        action="PROCEED",
        risk_score=0.1,
        explanation="low risk",
        timestamp=datetime.now(timezone.utc),
    )
    event_b = PolicyDecisionEvent(
        event_id="evt-b",
        call_session_id="call-b",
        tenant_id="tenant-beta",
        action="RECOMMEND_MFA_STEP_UP",
        risk_score=0.5,
        explanation="moderate risk",
        timestamp=datetime.now(timezone.utc),
    )

    engine.process_event(event_a)
    engine.process_event(event_b)

    alpha_entries = audit_logger.get_entries("tenant-alpha")
    beta_entries = audit_logger.get_entries("tenant-beta")

    assert all(e.tenant_id == "tenant-alpha" for e in alpha_entries)
    assert all(e.tenant_id == "tenant-beta" for e in beta_entries)
    assert len(alpha_entries) == 2  # 2 channels
    assert len(beta_entries) == 2
