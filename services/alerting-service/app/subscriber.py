"""
Pub/Sub subscriber abstraction for the alerting service.

The actual Pub/Sub client (e.g. Google Cloud Pub/Sub) is stubbed behind
an interface. For local development, an in-memory queue implements the
same interface, allowing the full consumer flow to be tested without
any external dependencies.

Design note: at-least-once delivery semantics from the publisher are
acceptable (DESIGN.md architecture note). Duplicate suppression happens
at the consumer side via the DeliveryStore, not here.
"""

from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from collections import deque
from typing import Callable

from models import PolicyDecisionEvent


# ---------------------------------------------------------------------------
# PubSubSubscriber — abstract interface
# ---------------------------------------------------------------------------

class PubSubSubscriber(ABC):
    """
    Abstract Pub/Sub subscriber. Consumes policy decision events from
    a topic and delivers them to a callback.

    The interface is intentionally simple: subscribe to a topic with a
    callback, and the implementation handles polling/pushing. The
    callback receives a PolicyDecisionEvent and must not raise — any
    errors should be handled internally by the engine.
    """

    @abstractmethod
    def subscribe(
        self,
        topic: str,
        callback: Callable[[PolicyDecisionEvent], None],
    ) -> None:
        """
        Register a callback for events on the given topic.

        Parameters
        ----------
        topic : str
            The topic/subscription to consume from.
        callback : Callable[[PolicyDecisionEvent], None]
            Function to invoke for each received event.
        """
        ...

    @abstractmethod
    def publish(self, topic: str, event: PolicyDecisionEvent) -> None:
        """
        Publish an event to a topic.

        For the real Pub/Sub client, this would be on the publisher side
        (a different service). Included in the interface so the
        InMemoryPubSub can be used for end-to-end testing without
        needing a separate publisher stub.
        """
        ...


# ---------------------------------------------------------------------------
# InMemoryPubSub — local dev / test implementation
# ---------------------------------------------------------------------------

class InMemoryPubSub(PubSubSubscriber):
    """
    In-memory Pub/Sub implementation for local development and testing.

    Events are published into an in-memory deque per topic. Subscribers
    are called synchronously when drain() is invoked — this makes tests
    deterministic (no background threads needed for testing).

    For the FastAPI background consumer loop, drain() is called
    periodically.
    """

    def __init__(self) -> None:
        self._queues: dict[str, deque[PolicyDecisionEvent]] = {}
        self._callbacks: dict[str, list[Callable[[PolicyDecisionEvent], None]]] = {}
        self._lock = threading.Lock()

    def subscribe(
        self,
        topic: str,
        callback: Callable[[PolicyDecisionEvent], None],
    ) -> None:
        with self._lock:
            if topic not in self._callbacks:
                self._callbacks[topic] = []
                self._queues[topic] = deque()
            self._callbacks[topic].append(callback)

    def publish(self, topic: str, event: PolicyDecisionEvent) -> None:
        with self._lock:
            if topic not in self._queues:
                self._queues[topic] = deque()
            self._queues[topic].append(event)

    def drain(self, topic: str) -> int:
        """
        Process all pending events for a topic by invoking registered
        callbacks. Returns the number of events processed.

        This is called synchronously in tests and periodically by the
        background consumer loop in main.py.
        """
        processed = 0
        while True:
            event = None
            with self._lock:
                q = self._queues.get(topic)
                if q:
                    event = q.popleft()
            if event is None:
                break
            for cb in self._callbacks.get(topic, []):
                cb(event)
            processed += 1
        return processed

    def pending_count(self, topic: str) -> int:
        """Test helper: number of unprocessed events on a topic."""
        with self._lock:
            return len(self._queues.get(topic, []))
