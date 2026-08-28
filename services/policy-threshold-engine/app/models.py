"""
Pydantic models for the policy-threshold-engine.

These models define the data contracts for:
- Per-tenant policy configuration (the rules table)
- Risk assessment input (consumed from risk-fusion-engine, never fetched directly)
- Policy decision output (the final action shown to the end user)
- Audit log entries (immutable records of every policy change)

Key design constraint (DESIGN.md §4.7):
  auto_block_enabled defaults to False for every tenant. This default is
  load-bearing — it ensures no tenant can receive BLOCK_PENDING_VERIFICATION
  unless they have explicitly opted in. Do not change this default.
"""

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Tenant policy configuration
# ---------------------------------------------------------------------------

class TenantPolicyConfig(BaseModel):
    """
    Per-tenant policy rule set. Keyed by tenant_id.

    Thresholds are compared against the fused risk_score (0.0-1.0) from
    the upstream risk-fusion-engine's RiskAssessmentResponse.

    auto_block_enabled defaults to False. This is a load-bearing default
    per DESIGN.md §4.7: the system NEVER unilaterally blocks a transaction
    unless the tenant has explicitly opted in. Do not make this opt-out.
    """
    tenant_id: str
    callback_verification_threshold: float = Field(
        default=0.40, ge=0.0, le=1.0,
        description="risk_score >= this -> RECOMMEND_CALLBACK_VERIFICATION",
    )
    supervisor_escalation_threshold: float = Field(
        default=0.70, ge=0.0, le=1.0,
        description="risk_score >= this -> RECOMMEND_SUPERVISOR_ESCALATION",
    )
    block_threshold: float = Field(
        default=0.90, ge=0.0, le=1.0,
        description=(
            "risk_score >= this AND auto_block_enabled=True -> "
            "BLOCK_PENDING_VERIFICATION"
        ),
    )
    auto_block_enabled: bool = Field(
        default=False,
        description=(
            "MUST default to False. Opt-in only. When False, the engine "
            "will NEVER output BLOCK_PENDING_VERIFICATION regardless of "
            "risk_score. See DESIGN.md §4.7."
        ),
    )
    policy_version: int = Field(
        default=1,
        description="Auto-incremented on each policy update.",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )


class TenantPolicyUpdate(BaseModel):
    """
    Partial update payload for a tenant's policy configuration.
    Only the fields provided will be updated; omitted fields retain their
    current values.
    """
    callback_verification_threshold: Optional[float] = Field(
        default=None, ge=0.0, le=1.0,
    )
    supervisor_escalation_threshold: Optional[float] = Field(
        default=None, ge=0.0, le=1.0,
    )
    block_threshold: Optional[float] = Field(
        default=None, ge=0.0, le=1.0,
    )
    auto_block_enabled: Optional[bool] = None


# ---------------------------------------------------------------------------
# Risk assessment input (consumed from risk-fusion-engine)
# ---------------------------------------------------------------------------

class RiskAssessmentInput(BaseModel):
    """
    The RiskAssessmentResponse from risk-fusion-engine, received as input.

    This service does NOT call risk-fusion-engine directly — it only
    consumes RiskAssessmentResponse objects it is given. The data flow
    is one-directional (DESIGN.md §5).
    """
    call_session_id: str
    risk_score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    actions: list[str] = Field(
        description="Original recommended actions from the fusion engine.",
    )
    explanation: str
    evaluated_at: str
    degraded: bool


class EvaluateRequest(BaseModel):
    """Top-level request to the /v1/evaluate endpoint."""
    tenant_id: str
    assessment: RiskAssessmentInput


# ---------------------------------------------------------------------------
# Policy decision output
# ---------------------------------------------------------------------------

class PolicyDecision(BaseModel):
    """
    The final action decision, after applying the tenant's policy rules
    to the risk-fusion-engine's assessment.

    policy_version stamps which version of the tenant's policy was applied,
    ensuring past assessments are not retroactively reinterpreted under a
    new policy version.
    """
    call_session_id: str
    tenant_id: str
    risk_score: float
    original_actions: list[str]
    final_action: str
    explanation: str
    policy_version: int
    decided_at: str


# ---------------------------------------------------------------------------
# Audit log entry
# ---------------------------------------------------------------------------

class AuditLogEntry(BaseModel):
    """
    Immutable record of a policy configuration change.

    Every policy change (threshold edits, auto_block toggling) writes one
    entry per changed field. These entries are the piece a bank's compliance
    team will ask to see (DESIGN.md §4.8).

    REVIEW FLAG: This model and the code paths that write these entries are
    flagged for human review before merge.
    """
    entry_id: str = Field(description="UUID, unique per entry.")
    tenant_id: str
    actor: str = Field(
        description=(
            "Identity of the admin who made the change. Assumed to arrive "
            "pre-verified from the upstream auth layer."
        ),
    )
    action: str = Field(
        description="e.g. UPDATE_THRESHOLD, TOGGLE_AUTO_BLOCK",
    )
    field_changed: str
    old_value: str
    new_value: str
    timestamp: datetime
