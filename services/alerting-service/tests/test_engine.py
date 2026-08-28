"""
End-to-end engine tests for the alerting service.

Verifies the full AlertEngine flow:
- Event → dispatch to all channels → audit entries created
- Single retry: channel that fails once then succeeds → delivery succeeds
- Single retry: channel that fails twice → both failures audited
- Message body is human-readable and contains key information
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from datetime import datetime, timezone

from audit import AuditLogger
from channels import StubSMSEmailChannel, UIPushChannel
from engine import AlertEngine
from interfaces import InMemoryAuditLog, InMemoryDeliveryStore
from models import PolicyDecisionEvent


def _make_event(
    event_id: str = "evt-engine-test",
    tenant_id: str = "tenant-bank-1",
    action: str = "RECOMMEND_CALLBACK_VERIFICATION",
) -> PolicyDecisionEvent:
    return PolicyDecisionEvent(
        event_id=event_id,
        call_session_id="call-engine-001",
        tenant_id=tenant_id,
        action=action,
        risk_score=0.85,
        explanation="synthesis artifacts detected (score=0.90)",
        timestamp=datetime.now(timezone.utc),
    )


def _make_engine(sms_email=None):
    ui_push = UIPushChannel()
    if sms_email is None:
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
# End-to-end: event → channels → audit
# -------------------------------------------------------------------

def test_end_to_end_dispatch():
    """
    Full flow: process an event, verify both channels received the
    alert, and audit entries were created for both.
    """
    engine, ui_push, sms_email, audit_log, _ = _make_engine()
    event = _make_event()

    dispatched = engine.process_event(event)

    assert dispatched == 2

    # UI push has the alert
    ui_alerts = ui_push.get_alerts("tenant-bank-1")
    assert len(ui_alerts) == 1
    assert ui_alerts[0].action == "RECOMMEND_CALLBACK_VERIFICATION"
    assert ui_alerts[0].event_id == "evt-engine-test"

    # SMS/email was "sent" (logged)
    sms_sent = sms_email.get_sent()
    assert len(sms_sent) == 1
    assert sms_sent[0].action == "RECOMMEND_CALLBACK_VERIFICATION"

    # Audit entries for both
    assert len(audit_log.all_entries) == 2


# -------------------------------------------------------------------
# Single retry: fail once then succeed
# -------------------------------------------------------------------

def test_single_retry_on_failure_then_success():
    """
    Channel fails on the first attempt, succeeds on retry.
    The alert should be delivered, and BOTH attempts should be audited.
    """
    sms_email = StubSMSEmailChannel()
    sms_email.set_failure_mode(max_failures=1)  # fail once, then succeed

    engine, ui_push, _, audit_log, _ = _make_engine(sms_email=sms_email)
    event = _make_event("evt-retry-success")

    dispatched = engine.process_event(event)
    assert dispatched == 2  # both channels dispatched

    # SMS channel: failed once, retried, succeeded
    assert sms_email.sent_count() == 1

    # Audit: ui_push (1 success) + sms_email (1 failure + 1 success) = 3
    sms_entries = [e for e in audit_log.all_entries if e.channel == "sms_email"]
    assert len(sms_entries) == 2
    assert sms_entries[0].status == "failed"   # first attempt
    assert sms_entries[1].status == "delivered" # retry succeeded


# -------------------------------------------------------------------
# Single retry: fail twice (give up)
# -------------------------------------------------------------------

def test_single_retry_exhausted():
    """
    Channel fails on both the first attempt and the retry.
    Both failures should be audited, and the event is still marked
    as delivered (we made our best effort; re-delivery on the next
    duplicate won't help).
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

    event = _make_event("evt-retry-exhausted")
    dispatched = engine.process_event(event)
    assert dispatched == 1  # channel was dispatched to (even though it failed)

    # Both attempts audited as failed
    entries = audit_log.all_entries
    assert len(entries) == 2
    assert all(e.status == "failed" for e in entries)

    # Event is marked delivered (best-effort exhausted)
    assert delivery_store.has_delivered("evt-retry-exhausted", "sms_email")

    # Re-processing the same event does nothing (idempotency)
    dispatched_2 = engine.process_event(event)
    assert dispatched_2 == 0


# -------------------------------------------------------------------
# Message body
# -------------------------------------------------------------------

def test_message_body_is_human_readable():
    """
    The alert message body should contain the action, call session,
    risk score, and explanation — not just a bare ID.
    """
    engine, ui_push, _, _, _ = _make_engine()
    event = _make_event()

    engine.process_event(event)

    alerts = ui_push.get_alerts("tenant-bank-1")
    body = alerts[0].message_body

    assert "RECOMMEND_CALLBACK_VERIFICATION" in body
    assert "call-engine-001" in body
    assert "0.85" in body
    assert "synthesis" in body.lower()


# -------------------------------------------------------------------
# Multiple tenants
# -------------------------------------------------------------------

def test_multiple_tenants_isolated():
    """Events from different tenants produce isolated alert sets."""
    engine, ui_push, sms_email, audit_log, _ = _make_engine()

    event_bank = _make_event("evt-bank", tenant_id="tenant-bank")
    event_telco = _make_event("evt-telco", tenant_id="tenant-telco")

    engine.process_event(event_bank)
    engine.process_event(event_telco)

    assert ui_push.alert_count("tenant-bank") == 1
    assert ui_push.alert_count("tenant-telco") == 1

    # Audit entries for each tenant
    bank_audit = [e for e in audit_log.all_entries if e.tenant_id == "tenant-bank"]
    telco_audit = [e for e in audit_log.all_entries if e.tenant_id == "tenant-telco"]
    assert len(bank_audit) == 2  # 2 channels
    assert len(telco_audit) == 2


# -------------------------------------------------------------------
# Empty channel list
# -------------------------------------------------------------------

def test_engine_with_no_channels():
    """An engine with no channels dispatches nothing (edge case)."""
    delivery_store = InMemoryDeliveryStore()
    audit_log = InMemoryAuditLog()
    audit_logger = AuditLogger(audit_log)
    engine = AlertEngine(
        channels=[],
        delivery_store=delivery_store,
        audit_logger=audit_logger,
    )

    event = _make_event("evt-no-channels")
    dispatched = engine.process_event(event)
    assert dispatched == 0
    assert len(audit_log.all_entries) == 0
