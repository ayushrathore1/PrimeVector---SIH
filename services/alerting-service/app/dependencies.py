"""
FastAPI dependency injection for the alerting service.

Wires up the AlertEngine with its dependencies (channels, delivery
store, audit log, pub/sub) as singletons, and provides
reset_dependencies() for test isolation.

Pattern follows enrollment-service/app/dependencies.py.
"""

from __future__ import annotations

from audit import AuditLogger
from channels import StubSMSEmailChannel, UIPushChannel
from engine import AlertEngine
from interfaces import InMemoryAuditLog, InMemoryDeliveryStore
from subscriber import InMemoryPubSub


# ---------------------------------------------------------------------------
# Singletons (module-level, created once at import time)
# ---------------------------------------------------------------------------

_ui_push_channel = UIPushChannel()
_sms_email_channel = StubSMSEmailChannel()
_delivery_store = InMemoryDeliveryStore()
_audit_log = InMemoryAuditLog()
_audit_logger = AuditLogger(_audit_log)
_pubsub = InMemoryPubSub()
_engine = AlertEngine(
    channels=[_ui_push_channel, _sms_email_channel],
    delivery_store=_delivery_store,
    audit_logger=_audit_logger,
)

# The topic name the policy-threshold-engine publishes to.
POLICY_DECISIONS_TOPIC = "policy-decisions"


# ---------------------------------------------------------------------------
# FastAPI dependency providers
# ---------------------------------------------------------------------------

def get_engine() -> AlertEngine:
    """FastAPI dependency: returns the singleton AlertEngine."""
    return _engine


def get_ui_push_channel() -> UIPushChannel:
    """FastAPI dependency: returns the singleton UIPushChannel."""
    return _ui_push_channel


def get_sms_email_channel() -> StubSMSEmailChannel:
    """FastAPI dependency: returns the singleton StubSMSEmailChannel."""
    return _sms_email_channel


def get_audit_logger() -> AuditLogger:
    """FastAPI dependency: returns the singleton AuditLogger."""
    return _audit_logger


def get_pubsub() -> InMemoryPubSub:
    """FastAPI dependency: returns the singleton InMemoryPubSub."""
    return _pubsub


# ---------------------------------------------------------------------------
# Test support
# ---------------------------------------------------------------------------

def reset_dependencies() -> None:
    """Reset all dependencies to fresh instances (for test isolation)."""
    global _ui_push_channel, _sms_email_channel, _delivery_store, _audit_log, _audit_logger, _pubsub, _engine
    _ui_push_channel = UIPushChannel()
    _sms_email_channel = StubSMSEmailChannel()
    _delivery_store = InMemoryDeliveryStore()
    _audit_log = InMemoryAuditLog()
    _audit_logger = AuditLogger(_audit_log)
    _pubsub = InMemoryPubSub()
    _engine = AlertEngine(
        channels=[_ui_push_channel, _sms_email_channel],
        delivery_store=_delivery_store,
        audit_logger=_audit_logger,
    )
