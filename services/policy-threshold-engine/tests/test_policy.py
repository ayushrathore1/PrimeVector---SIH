"""
Tests for the policy evaluation logic.

The critical test in this file is test_auto_block_disabled_never_blocks:
it is a property-based test (Hypothesis, 200 examples) that proves a
tenant with auto_block_enabled=False NEVER receives
BLOCK_PENDING_VERIFICATION regardless of risk_score, including at 1.0.

This is the §4.7 safety invariant — if this test fails, the system's
liability model is broken.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from hypothesis import given, strategies as st, settings

from models import TenantPolicyConfig
from policy import evaluate_policy


# =====================================================================
# CRITICAL SAFETY TEST — §4.7 liability invariant
# =====================================================================

@given(risk_score=st.floats(min_value=0.0, max_value=1.0))
@settings(max_examples=200)
def test_auto_block_disabled_never_blocks(risk_score):
    """
    A tenant with auto_block_enabled=False must NEVER receive
    BLOCK_PENDING_VERIFICATION, regardless of risk_score.

    This is the load-bearing invariant from DESIGN.md §4.7:
    "The system NEVER unilaterally blocks a transaction" unless the
    tenant has explicitly opted in.

    Tested across the full [0.0, 1.0] range via Hypothesis.
    """
    config = TenantPolicyConfig(
        tenant_id="test-tenant",
        callback_verification_threshold=0.40,
        supervisor_escalation_threshold=0.70,
        block_threshold=0.90,
        auto_block_enabled=False,  # <-- the critical flag
    )
    result = evaluate_policy(risk_score, config)
    assert result != "BLOCK_PENDING_VERIFICATION", (
        f"SAFETY VIOLATION: auto_block_enabled=False but got "
        f"BLOCK_PENDING_VERIFICATION at risk_score={risk_score}"
    )


def test_auto_block_disabled_never_blocks_at_max_score():
    """
    Explicit edge case: risk_score=1.0 with auto_block_enabled=False
    must still NOT produce BLOCK_PENDING_VERIFICATION.

    This is the exact scenario the requirement calls out.
    """
    config = TenantPolicyConfig(
        tenant_id="test-tenant",
        callback_verification_threshold=0.40,
        supervisor_escalation_threshold=0.70,
        block_threshold=0.90,
        auto_block_enabled=False,
    )
    result = evaluate_policy(1.0, config)
    assert result != "BLOCK_PENDING_VERIFICATION"
    # At score 1.0, the highest non-block action should be escalation
    assert result == "RECOMMEND_SUPERVISOR_ESCALATION"


@given(
    risk_score=st.floats(min_value=0.0, max_value=1.0),
    cb_thresh=st.floats(min_value=0.0, max_value=1.0),
    esc_thresh=st.floats(min_value=0.0, max_value=1.0),
    blk_thresh=st.floats(min_value=0.0, max_value=1.0),
)
@settings(max_examples=200)
def test_auto_block_disabled_never_blocks_any_thresholds(
    risk_score, cb_thresh, esc_thresh, blk_thresh
):
    """
    Even with arbitrary threshold configurations, auto_block_enabled=False
    must never produce BLOCK_PENDING_VERIFICATION.
    """
    config = TenantPolicyConfig(
        tenant_id="test-tenant",
        callback_verification_threshold=cb_thresh,
        supervisor_escalation_threshold=esc_thresh,
        block_threshold=blk_thresh,
        auto_block_enabled=False,
    )
    result = evaluate_policy(risk_score, config)
    assert result != "BLOCK_PENDING_VERIFICATION"


# =====================================================================
# Auto-block enabled behaviour
# =====================================================================

def test_auto_block_enabled_blocks_above_threshold():
    """When auto_block is enabled and score >= threshold, block."""
    config = TenantPolicyConfig(
        tenant_id="test-tenant",
        block_threshold=0.90,
        auto_block_enabled=True,
    )
    result = evaluate_policy(0.95, config)
    assert result == "BLOCK_PENDING_VERIFICATION"


def test_auto_block_enabled_blocks_at_exact_threshold():
    """Block at exactly the threshold (>=, not >)."""
    config = TenantPolicyConfig(
        tenant_id="test-tenant",
        block_threshold=0.90,
        auto_block_enabled=True,
    )
    result = evaluate_policy(0.90, config)
    assert result == "BLOCK_PENDING_VERIFICATION"


def test_auto_block_enabled_does_not_block_below_threshold():
    """When enabled but score < threshold, don't block — use RECOMMEND_*."""
    config = TenantPolicyConfig(
        tenant_id="test-tenant",
        callback_verification_threshold=0.40,
        supervisor_escalation_threshold=0.70,
        block_threshold=0.90,
        auto_block_enabled=True,
    )
    result = evaluate_policy(0.85, config)
    assert result != "BLOCK_PENDING_VERIFICATION"
    assert result == "RECOMMEND_SUPERVISOR_ESCALATION"


# =====================================================================
# Threshold-based action selection
# =====================================================================

def test_escalation_threshold():
    """Score >= escalation threshold returns RECOMMEND_SUPERVISOR_ESCALATION."""
    config = TenantPolicyConfig(
        tenant_id="test-tenant",
        callback_verification_threshold=0.40,
        supervisor_escalation_threshold=0.70,
        auto_block_enabled=False,
    )
    result = evaluate_policy(0.75, config)
    assert result == "RECOMMEND_SUPERVISOR_ESCALATION"


def test_callback_threshold():
    """Score >= callback threshold but < escalation returns RECOMMEND_CALLBACK_VERIFICATION."""
    config = TenantPolicyConfig(
        tenant_id="test-tenant",
        callback_verification_threshold=0.40,
        supervisor_escalation_threshold=0.70,
        auto_block_enabled=False,
    )
    result = evaluate_policy(0.50, config)
    assert result == "RECOMMEND_CALLBACK_VERIFICATION"


def test_below_all_thresholds():
    """Score below all thresholds returns PROCEED."""
    config = TenantPolicyConfig(
        tenant_id="test-tenant",
        callback_verification_threshold=0.40,
        supervisor_escalation_threshold=0.70,
        auto_block_enabled=False,
    )
    result = evaluate_policy(0.20, config)
    assert result == "PROCEED"


def test_zero_score_always_proceeds():
    """A zero risk score should always produce PROCEED."""
    config = TenantPolicyConfig(
        tenant_id="test-tenant",
        auto_block_enabled=False,
    )
    result = evaluate_policy(0.0, config)
    assert result == "PROCEED"


# =====================================================================
# Severity ordering / threshold precedence
# =====================================================================

def test_block_takes_precedence_over_escalation():
    """When auto_block is enabled and score exceeds both block and escalation
    thresholds, block wins (highest severity)."""
    config = TenantPolicyConfig(
        tenant_id="test-tenant",
        supervisor_escalation_threshold=0.70,
        block_threshold=0.90,
        auto_block_enabled=True,
    )
    result = evaluate_policy(0.95, config)
    assert result == "BLOCK_PENDING_VERIFICATION"


def test_escalation_takes_precedence_over_callback():
    """When score exceeds both escalation and callback thresholds,
    escalation wins."""
    config = TenantPolicyConfig(
        tenant_id="test-tenant",
        callback_verification_threshold=0.40,
        supervisor_escalation_threshold=0.70,
        auto_block_enabled=False,
    )
    result = evaluate_policy(0.80, config)
    assert result == "RECOMMEND_SUPERVISOR_ESCALATION"


# =====================================================================
# Default configuration
# =====================================================================

def test_default_auto_block_is_false():
    """
    Verify that the load-bearing default for auto_block_enabled is False.
    If this test fails, someone changed the default — which violates §4.7.
    """
    config = TenantPolicyConfig(tenant_id="test-tenant")
    assert config.auto_block_enabled is False, (
        "CRITICAL: auto_block_enabled must default to False (DESIGN.md §4.7)"
    )


def test_default_thresholds():
    """Verify default thresholds are reasonable and match fusion engine's."""
    config = TenantPolicyConfig(tenant_id="test-tenant")
    assert config.callback_verification_threshold == 0.40
    assert config.supervisor_escalation_threshold == 0.70
    assert config.block_threshold == 0.90
    assert config.auto_block_enabled is False
    assert config.policy_version == 1
