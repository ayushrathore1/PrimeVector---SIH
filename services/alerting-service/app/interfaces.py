"""
Abstract interfaces for the alerting service's external dependencies.

These exist so the alert engine (engine.py) never couples to a specific
message broker, notification channel, storage backend, or audit sink.
Each has a stub/in-memory implementation for local development and
testing; production implementations are provided by separate packages.

Pattern follows enrollment-service/app/interfaces.py — ABCs with
explicit stub implementations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


# ---------------------------------------------------------------------------
# Channel — abstract delivery channel for alerts
# ---------------------------------------------------------------------------

class Channel(ABC):
    """
    Abstract alert delivery channel.

    Concrete implementations: UIPushChannel (in-memory, pollable),
    StubSMSEmailChannel (logs what would be sent, no real provider).

    Each channel has a name (used as the idempotency key alongside
    event_id) and a send() method that returns a DeliveryResult.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique channel identifier, e.g. 'ui_push', 'sms_email'."""
        ...

    @abstractmethod
    def send(self, alert: Any) -> Any:
        """
        Deliver an alert via this channel.

        Parameters
        ----------
        alert : Alert
            The alert to deliver.

        Returns
        -------
        DeliveryResult
            Outcome of the delivery attempt (delivered / failed).
        """
        ...


# ---------------------------------------------------------------------------
# DeliveryStore — tracks which (event_id, channel) pairs have been
# delivered, forming the consumer-side idempotency gate.
# ---------------------------------------------------------------------------

class DeliveryStore(ABC):
    """
    Tracks delivered (event_id, channel) pairs to enforce idempotent
    delivery. The same event_id delivered twice must not send duplicate
    alerts — this store is the enforcement mechanism.

    At-least-once delivery semantics from the publisher are acceptable
    (DESIGN.md architecture note), but duplicates must be suppressed
    here at the consumer, not prevented at the publisher.
    """

    @abstractmethod
    def has_delivered(self, event_id: str, channel: str) -> bool:
        """Check whether this (event_id, channel) was already delivered."""
        ...

    @abstractmethod
    def mark_delivered(self, event_id: str, channel: str) -> None:
        """Record that this (event_id, channel) has been delivered."""
        ...


class InMemoryDeliveryStore(DeliveryStore):
    """In-memory idempotency store for local development and testing."""

    def __init__(self) -> None:
        self._delivered: set[tuple[str, str]] = set()

    def has_delivered(self, event_id: str, channel: str) -> bool:
        return (event_id, channel) in self._delivered

    def mark_delivered(self, event_id: str, channel: str) -> None:
        self._delivered.add((event_id, channel))


# ---------------------------------------------------------------------------
# AuditLog — abstract audit sink
# ---------------------------------------------------------------------------

class AuditLog(ABC):
    """
    Abstract audit log sink. Every alert sent (or attempted) is written
    here with channel, hashed recipient (never raw contact info), and
    delivery status — per DESIGN.md §4.8.
    """

    @abstractmethod
    def write(self, entry: Any) -> None:
        """Write an audit entry."""
        ...

    @abstractmethod
    def get_entries(self, tenant_id: str) -> list:
        """Retrieve audit entries for a tenant."""
        ...


class InMemoryAuditLog(AuditLog):
    """In-memory audit log for local development and testing."""

    def __init__(self) -> None:
        self._entries: list = []

    def write(self, entry: Any) -> None:
        self._entries.append(entry)

    def get_entries(self, tenant_id: str) -> list:
        return [e for e in self._entries if e.tenant_id == tenant_id]

    @property
    def all_entries(self) -> list:
        """Test helper: return all entries regardless of tenant."""
        return list(self._entries)
