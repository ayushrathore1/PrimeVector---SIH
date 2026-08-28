"""
Policy evaluation logic for the policy-threshold-engine.

This is a pure function with no side effects, no state, and no I/O.
Given a risk_score and a tenant's policy configuration, it returns the
single final action to surface to the end user.

Hard constraint (DESIGN.md §4.7, liability-driven):
  If auto_block_enabled is False, this function NEVER returns
  BLOCK_PENDING_VERIFICATION, regardless of risk_score — even at 1.0.
  This is enforced by the code structure (the block branch is gated
  behind an explicit `if auto_block_enabled`) and verified by a
  property-based test covering the full [0.0, 1.0] score range.
"""

from models import TenantPolicyConfig


def evaluate_policy(risk_score: float, config: TenantPolicyConfig) -> str:
    """
    Determine the final action for an assessment given the tenant's policy.

    Evaluation order (highest severity first):

    1. BLOCK_PENDING_VERIFICATION — only if auto_block_enabled=True AND
       risk_score >= block_threshold. If auto_block_enabled is False,
       this branch is unreachable regardless of score.
    2. RECOMMEND_SUPERVISOR_ESCALATION — risk_score >= supervisor threshold.
    3. RECOMMEND_CALLBACK_VERIFICATION — risk_score >= callback threshold.
    4. PROCEED — below all thresholds.

    Returns exactly one action string.
    """
    # --- Auto-block gate (§4.7) ---
    # This is the liability boundary. The `and` short-circuits: if the
    # tenant has not opted in, we never even evaluate the threshold.
    if config.auto_block_enabled and risk_score >= config.block_threshold:
        return "BLOCK_PENDING_VERIFICATION"

    # --- Recommend-only actions (always available) ---
    if risk_score >= config.supervisor_escalation_threshold:
        return "RECOMMEND_SUPERVISOR_ESCALATION"

    if risk_score >= config.callback_verification_threshold:
        return "RECOMMEND_CALLBACK_VERIFICATION"

    return "PROCEED"
