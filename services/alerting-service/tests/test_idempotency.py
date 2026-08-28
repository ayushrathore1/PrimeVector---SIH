"""
Idempotency tests for the alerting service.

THE KEY REQUIREMENT: the same event ID delivered twice must not send
duplicate alerts. This test publishes the same event twice and asserts
only one delivery per channel.

This tests consumer-side dedup (at-least-once from publisher,
exactly-once at consumer) — per DESIGN.md architecture note.
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
from subscriber import InMemoryPubSub


def _make_event(event_id: str = "evt-001") -> PolicyDecisionEvent:
    """Helper: create a policy decision event with a given event_id."""
    return PolicyDecisionEvent(
        event_id=event_id,
        call_session_id="call-abc-123",
        tenant_id="tenant-bank-1",
        action="RECOMMEND_CALLBACK_VERIFICATION",
        risk_score=0.85,
        explanation="synthesis artifacts detected",
        timestamp=datetime.now(timezone.utc),
    )


def _make_engine():
    """Helper: create a fresh engine with all dependencies."""
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
# Core idempotency test: same event_id twice → one delivery per channel
# -------------------------------------------------------------------

def test_duplicate_event_produces_single_delivery_per_channel():
    """
    Publish the same PolicyDecisionEvent (same event_id) twice.
    Assert exactly one delivery per channel.

    This is THE idempotency test required by the spec.
    """
    engine, ui_push, sms_email, audit_log, _ = _make_engine()
    event = _make_event("evt-duplicate-test")

    # First delivery — should dispatch to both channels
    dispatched_1 = engine.process_event(event)
    assert dispatched_1 == 2  # ui_push + sms_email

    # Second delivery of the SAME event — should dispatch to zero channels
    dispatched_2 = engine.process_event(event)
    assert dispatched_2 == 0

    # Assert exactly one alert per channel
    assert ui_push.alert_count("tenant-bank-1") == 1
    assert sms_email.sent_count() == 1


def test_duplicate_event_via_pubsub_produces_single_delivery():
    """
    Same test but going through the InMemoryPubSub layer — verifies
    the full consumer path, not just the engine directly.
    """
    engine, ui_push, sms_email, audit_log, _ = _make_engine()
    pubsub = InMemoryPubSub()

    # Subscribe the engine
    pubsub.subscribe("policy-decisions", engine.process_event)

    event = _make_event("evt-pubsub-dup")

    # Publish the same event TWICE (simulating at-least-once delivery)
    pubsub.publish("policy-decisions", event)
    pubsub.publish("policy-decisions", event)

    # Drain — both messages are processed
    processed = pubsub.drain("policy-decisions")
    assert processed == 2  # both messages were consumed

    # But only one delivery per channel
    assert ui_push.alert_count("tenant-bank-1") == 1
    assert sms_email.sent_count() == 1


def test_different_event_ids_are_not_deduplicated():
    """
    Two events with DIFFERENT event_ids should both be delivered —
    idempotency is per event_id, not per call_session_id or content.
    """
    engine, ui_push, sms_email, _, _ = _make_engine()

    event_a = _make_event("evt-aaa")
    event_b = _make_event("evt-bbb")

    engine.process_event(event_a)
    engine.process_event(event_b)

    # Both events delivered to both channels
    assert ui_push.alert_count("tenant-bank-1") == 2
    assert sms_email.sent_count() == 2


def test_idempotency_is_per_channel():
    """
    Verify that the idempotency key is (event_id, channel), not just
    event_id — i.e. each channel tracks independently.
    """
    # Use a single-channel engine to verify independence
    ui_push = UIPushChannel()
    delivery_store = InMemoryDeliveryStore()
    audit_log = InMemoryAuditLog()
    audit_logger = AuditLogger(audit_log)

    engine_ui_only = AlertEngine(
        channels=[ui_push],
        delivery_store=delivery_store,
        audit_logger=audit_logger,
    )

    event = _make_event("evt-per-channel")

    dispatched = engine_ui_only.process_event(event)
    assert dispatched == 1
    assert ui_push.alert_count("tenant-bank-1") == 1

    # Now add sms_email to a NEW engine sharing the SAME delivery store
    sms_email = StubSMSEmailChannel()
    engine_both = AlertEngine(
        channels=[ui_push, sms_email],
        delivery_store=delivery_store,
        audit_logger=audit_logger,
    )

    # ui_push should be skipped (already delivered), sms_email should go
    dispatched = engine_both.process_event(event)
    assert dispatched == 1  # only sms_email
    assert ui_push.alert_count("tenant-bank-1") == 1  # still 1
    assert sms_email.sent_count() == 1


def test_audit_entries_created_only_for_first_delivery():
    """
    Duplicate events should not produce additional audit entries for
    skipped channels.
    """
    engine, _, _, audit_log, _ = _make_engine()
    event = _make_event("evt-audit-dup")

    engine.process_event(event)
    entries_after_first = len(audit_log.all_entries)

    engine.process_event(event)
    entries_after_second = len(audit_log.all_entries)

    # No new audit entries for the duplicate
    assert entries_after_second == entries_after_first
    # Should have exactly 2 entries (one per channel) from the first delivery
    assert entries_after_first == 2
