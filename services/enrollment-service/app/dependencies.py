"""
FastAPI dependency injection for the enrollment service.

Wires up the EnrollmentService with its dependencies (store, liveness
checker, model registry) as singletons, and provides the RBAC
enforcement dependency that all mutation endpoints use.
"""

from dataclasses import dataclass

from fastapi import Header, HTTPException, Request

from enrollment import EnrollmentService
from interfaces import StubLivenessChecker, StubModelRegistry
from store import InMemoryVoiceprintStore


# ---------------------------------------------------------------------------
# Singletons (module-level, created once at import time)
# ---------------------------------------------------------------------------

_store = InMemoryVoiceprintStore()
_liveness_checker = StubLivenessChecker()
_model_registry = StubModelRegistry()
_enrollment_service = EnrollmentService(
    store=_store,
    liveness_checker=_liveness_checker,
    model_registry=_model_registry,
)


def get_enrollment_service() -> EnrollmentService:
    """FastAPI dependency: returns the singleton EnrollmentService."""
    return _enrollment_service


def get_store() -> InMemoryVoiceprintStore:
    """FastAPI dependency: returns the singleton store (for audit log endpoint)."""
    return _store


# ---------------------------------------------------------------------------
# For testing: allow swapping the liveness checker
# ---------------------------------------------------------------------------

def set_liveness_checker(checker) -> None:
    """Replace the liveness checker (for testing with StubLivenessChecker(force_fail=True))."""
    global _enrollment_service, _store, _model_registry
    _enrollment_service = EnrollmentService(
        store=_store,
        liveness_checker=checker,
        model_registry=_model_registry,
    )


def reset_dependencies() -> None:
    """Reset all dependencies to fresh instances (for test isolation)."""
    global _store, _liveness_checker, _model_registry, _enrollment_service
    _store = InMemoryVoiceprintStore()
    _liveness_checker = StubLivenessChecker()
    _model_registry = StubModelRegistry()
    _enrollment_service = EnrollmentService(
        store=_store,
        liveness_checker=_liveness_checker,
        model_registry=_model_registry,
    )


# ---------------------------------------------------------------------------
# RBAC dependency
# ---------------------------------------------------------------------------

@dataclass
class ActorContext:
    """Extracted and validated actor identity from request headers."""
    actor_id: str
    actor_role: str


def require_tenant_admin(
    x_actor_id: str = Header(None),
    x_actor_role: str = Header(None),
) -> ActorContext:
    """
    FastAPI dependency that enforces tenant-admin RBAC at the API layer.

    Extracts X-Actor-Id and X-Actor-Role headers and rejects requests
    that are not from a tenant_admin. This is enforced here (not just
    in a comment) and tested in test_api.py.

    The domain logic (enrollment.py) performs a defense-in-depth re-check,
    but this dependency is the primary enforcement point.
    """
    if not x_actor_id or not x_actor_role:
        raise HTTPException(
            status_code=403,
            detail="Missing required headers: X-Actor-Id and X-Actor-Role",
        )
    if x_actor_role != "tenant_admin":
        raise HTTPException(
            status_code=403,
            detail=(
                f"Only tenant_admin can perform this operation, "
                f"got role: {x_actor_role}"
            ),
        )
    return ActorContext(actor_id=x_actor_id, actor_role=x_actor_role)
