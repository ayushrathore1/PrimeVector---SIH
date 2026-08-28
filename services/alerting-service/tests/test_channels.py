"""
Tests for alert delivery channels.

Verifies the Channel interface contract for both concrete implementations:
- UIPushChannel: alert appears in the retrievable per-tenant list
- StubSMSEmailChannel: logs the message, returns delivered, records in
  the in-memory sent list for test assertions
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from datetime import datetime, timezone

from channels import StubSMSEmailChannel, UIPushChannel
from models import Alert, DeliveryStatus


def _make_alert(
    tenant_id: str = "tenant-bank-1",
    channel: str = "test",
    event_id: str = "evt-001",
) -> Alert:
    """Helper: create an alert for testing."""
    return Alert(
        alert_id="alert-001",
        event_id=event_id,
        call_session_id="call-abc-123",
        tenant_id=tenant_id,
        action="RECOMMEND_CALLBACK_VERIFICATION",
        channel=channel,
        recipient="sms_email:tenant-bank-1:staff",
        message_body="Test alert message",
        created_at=datetime.now(timezone.utc),
    )


# -------------------------------------------------------------------
# UIPushChannel
# -------------------------------------------------------------------

class TestUIPushChannel:

    def test_name_is_ui_push(self):
        ch = UIPushChannel()
        assert ch.name == "ui_push"

    def test_send_returns_delivered(self):
        ch = UIPushChannel()
        alert = _make_alert(channel="ui_push")
        result = ch.send(alert)
        assert result.status == DeliveryStatus.DELIVERED
        assert result.channel == "ui_push"

    def test_sent_alert_appears_in_tenant_list(self):
        ch = UIPushChannel()
        alert = _make_alert(tenant_id="tenant-x", channel="ui_push")
        ch.send(alert)

        alerts = ch.get_alerts("tenant-x")
        assert len(alerts) == 1
        assert alerts[0].alert_id == "alert-001"
        assert alerts[0].tenant_id == "tenant-x"

    def test_alerts_are_tenant_scoped(self):
        ch = UIPushChannel()
        alert_a = _make_alert(tenant_id="tenant-a", channel="ui_push")
        alert_b = _make_alert(tenant_id="tenant-b", channel="ui_push")
        ch.send(alert_a)
        ch.send(alert_b)

        assert ch.alert_count("tenant-a") == 1
        assert ch.alert_count("tenant-b") == 1
        assert ch.alert_count("tenant-c") == 0

    def test_multiple_alerts_same_tenant(self):
        ch = UIPushChannel()
        for i in range(5):
            alert = Alert(
                alert_id=f"alert-{i}",
                event_id=f"evt-{i}",
                call_session_id="call-abc",
                tenant_id="tenant-1",
                action="RECOMMEND_MFA_STEP_UP",
                channel="ui_push",
                recipient="ui_push:tenant-1:staff",
                message_body=f"Alert {i}",
                created_at=datetime.now(timezone.utc),
            )
            ch.send(alert)
        assert ch.alert_count("tenant-1") == 5


# -------------------------------------------------------------------
# StubSMSEmailChannel
# -------------------------------------------------------------------

class TestStubSMSEmailChannel:

    def test_name_is_sms_email(self):
        ch = StubSMSEmailChannel()
        assert ch.name == "sms_email"

    def test_send_returns_delivered(self):
        ch = StubSMSEmailChannel()
        alert = _make_alert(channel="sms_email")
        result = ch.send(alert)
        assert result.status == DeliveryStatus.DELIVERED
        assert result.channel == "sms_email"

    def test_sent_alert_recorded_in_memory(self):
        ch = StubSMSEmailChannel()
        alert = _make_alert(channel="sms_email")
        ch.send(alert)

        sent = ch.get_sent()
        assert len(sent) == 1
        assert sent[0].alert_id == "alert-001"

    def test_stub_does_not_actually_send(self):
        """
        The stub channel's purpose is to log, not send. Verify it
        returns a result indicating it was stubbed.
        """
        ch = StubSMSEmailChannel()
        alert = _make_alert(channel="sms_email")
        result = ch.send(alert)
        assert "stub" in result.detail.lower()

    def test_failure_mode_then_recovery(self):
        """
        StubSMSEmailChannel supports a test mode where the first N
        sends fail, then subsequent sends succeed. This is used to
        test the single-retry logic in engine.py.
        """
        ch = StubSMSEmailChannel()
        ch.set_failure_mode(max_failures=1)

        alert = _make_alert(channel="sms_email")

        # First send fails
        result_1 = ch.send(alert)
        assert result_1.status == DeliveryStatus.FAILED

        # Second send succeeds
        result_2 = ch.send(alert)
        assert result_2.status == DeliveryStatus.DELIVERED
