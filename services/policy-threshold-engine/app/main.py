"""
Policy Threshold Engine — FastAPI service.

This is the §4.7 liability layer: it sits downstream of risk-fusion-engine,
receives RiskAssessmentResponse objects, and applies per-tenant configurable
rules to determine the FINAL action shown to the end user.

This service does NOT call risk-fusion-engine directly — it only consumes
RiskAssessmentResponse objects it is given. Data flow is one-directional.

Auth model: tenant_admin claims arrive pre-verified from an upstream auth
layer (not implemented here). We check the X-Tenant-Admin header and
reject admin operations if it's not "true". Actor identity for audit
logging comes from the X-Actor-Identity header.
"""

from datetime import datetime, timezone

from fastapi import FastAPI, Header, HTTPException, Request

from models import (
    AuditLogEntry,
    EvaluateRequest,
    PolicyDecision,
    RiskAssessmentInput,
    TenantPolicyConfig,
    TenantPolicyUpdate,
)
from policy import evaluate_policy
from store import TenantPolicyStore
from audit import AuditLog

app = FastAPI(title="policy-threshold-engine", version="0.1.0")

# In-memory singletons for this reference implementation.
# Production: inject these as dependencies backed by a real store.
_store = TenantPolicyStore()
_audit_log = AuditLog()


def _require_tenant_admin(x_tenant_admin: str | None) -> None:
    """
    Verify that the incoming request carries a pre-verified tenant_admin
    claim. We do NOT implement auth here — we assume the upstream auth
    layer has already verified the claim and set the header.

    Raises HTTP 403 if the claim is missing or not "true".
    """
    if x_tenant_admin is None or x_tenant_admin.lower() != "true":
        raise HTTPException(
            status_code=403,
            detail="Tenant admin authorization required.",
        )


def _require_actor_identity(x_actor_identity: str | None) -> str:
    """
    Extract the actor identity from the pre-verified header.
    Required for audit logging on admin operations.
    """
    if not x_actor_identity:
        raise HTTPException(
            status_code=400,
            detail="X-Actor-Identity header is required for admin operations.",
        )
    return x_actor_identity


# -----------------------------------------------------------------------
# Evaluate endpoint — the core purpose of this service
# -----------------------------------------------------------------------

@app.post("/v1/evaluate", response_model=PolicyDecision)
def evaluate(req: EvaluateRequest) -> PolicyDecision:
    """
    Apply the tenant's current policy to a RiskAssessmentResponse and
    return the final action.

    The policy_version stamped on the response records which version of
    the tenant's policy was applied, ensuring past assessments are not
    retroactively reinterpreted under a new policy version.
    """
    config = _store.get_or_create_default(req.tenant_id)
    final_action = evaluate_policy(req.assessment.risk_score, config)

    return PolicyDecision(
        call_session_id=req.assessment.call_session_id,
        tenant_id=req.tenant_id,
        risk_score=req.assessment.risk_score,
        original_actions=req.assessment.actions,
        final_action=final_action,
        explanation=req.assessment.explanation,
        policy_version=config.policy_version,
        decided_at=datetime.now(timezone.utc).isoformat(),
    )


# -----------------------------------------------------------------------
# Policy admin endpoints
# -----------------------------------------------------------------------

@app.get("/v1/tenants/{tenant_id}/policy", response_model=TenantPolicyConfig)
def get_policy(
    tenant_id: str,
    x_tenant_admin: str | None = Header(default=None),
) -> TenantPolicyConfig:
    """Return the current policy configuration for a tenant."""
    _require_tenant_admin(x_tenant_admin)
    config = _store.get_or_create_default(tenant_id)
    return config


@app.put("/v1/tenants/{tenant_id}/policy", response_model=TenantPolicyConfig)
def update_policy(
    tenant_id: str,
    updates: TenantPolicyUpdate,
    x_tenant_admin: str | None = Header(default=None),
    x_actor_identity: str | None = Header(default=None),
) -> TenantPolicyConfig:
    """
    Update the policy configuration for a tenant.

    Every changed field produces an immutable audit log entry with actor
    identity, old value, new value, and timestamp. This is the code path
    a bank's compliance team will inspect.

    REVIEW FLAG: This endpoint and the audit log entries it produces are
    flagged for human review before merge.

    Policy config changes take effect for new assessments only; they do
    not retroactively reinterpret past RiskAssessmentResponses.
    """
    _require_tenant_admin(x_tenant_admin)
    actor = _require_actor_identity(x_actor_identity)

    new_config, audit_entries = _store.upsert_policy(
        tenant_id=tenant_id,
        updates=updates,
        actor=actor,
    )

    # Persist audit entries — this is the compliance-critical write.
    for entry in audit_entries:
        _audit_log.append(entry)

    return new_config


# -----------------------------------------------------------------------
# Audit log endpoint
# -----------------------------------------------------------------------

@app.get("/v1/tenants/{tenant_id}/audit-log", response_model=list[AuditLogEntry])
def get_audit_log(
    tenant_id: str,
    x_tenant_admin: str | None = Header(default=None),
) -> list[AuditLogEntry]:
    """Return audit log entries for a tenant."""
    _require_tenant_admin(x_tenant_admin)
    return _audit_log.get_entries(tenant_id=tenant_id)


# -----------------------------------------------------------------------
# Health check
# -----------------------------------------------------------------------

@app.get("/healthz")
def healthz():
    """Liveness check. This service is stateless beyond its in-memory stores."""
    return {"status": "ok"}
