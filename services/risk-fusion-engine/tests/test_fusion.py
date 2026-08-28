"""
Tests for the risk fusion engine.

These are not "does it run" tests. For a component that can trigger a
recommendation to block a financial transaction, the properties that
matter are: determinism, monotonicity, and bounded output. Example-based
tests alone would not have caught a regression in any of these -- that's
why the core of this suite is property-based (Hypothesis).
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from hypothesis import given, strategies as st, settings
from fusion import Signal, fuse, HIGH_RISK_ACTION_THRESHOLD


def signal_strategy(available=True):
    return st.builds(
        Signal,
        score=st.floats(min_value=0.0, max_value=1.0),
        confidence=st.floats(min_value=0.0, max_value=1.0),
        available=st.just(available),
        detail=st.just(""),
    )


unavailable_signal = Signal(score=0.0, confidence=0.0, available=False)


# ---------------------------------------------------------------------
# Property: determinism. Same inputs must always produce the same output.
# This is a hard requirement (DESIGN.md 4.8) -- an auditor asking "why was
# this call flagged six months ago" needs a reproducible answer.
# ---------------------------------------------------------------------
@given(signal_strategy(), signal_strategy(), signal_strategy())
@settings(max_examples=200)
def test_determinism(synthesis, speaker_match, contextual):
    r1 = fuse(synthesis, speaker_match, contextual)
    r2 = fuse(synthesis, speaker_match, contextual)
    assert r1 == r2


# ---------------------------------------------------------------------
# Property: output is always bounded to [0, 1].
# ---------------------------------------------------------------------
@given(signal_strategy(), signal_strategy(), signal_strategy())
@settings(max_examples=200)
def test_bounded_output(synthesis, speaker_match, contextual):
    result = fuse(synthesis, speaker_match, contextual)
    assert 0.0 <= result.risk_score <= 1.0
    assert 0.0 <= result.confidence <= 1.0


# ---------------------------------------------------------------------
# Property: monotonicity. Raising either acoustic signal's score, holding
# everything else fixed, must never DECREASE the fused risk score. If this
# property breaks, the fusion math is unsound in a way that would be very
# hard to spot from example tests alone.
# ---------------------------------------------------------------------
@given(
    base_score=st.floats(min_value=0.0, max_value=0.8),
    increase=st.floats(min_value=0.01, max_value=0.2),
    confidence=st.floats(min_value=0.5, max_value=1.0),
    contextual=signal_strategy(),
)
@settings(max_examples=200)
def test_monotonic_in_synthesis_score(base_score, increase, confidence, contextual):
    speaker_match = unavailable_signal
    low = Signal(score=base_score, confidence=confidence, available=True)
    high = Signal(score=min(1.0, base_score + increase), confidence=confidence, available=True)

    r_low = fuse(low, speaker_match, contextual)
    r_high = fuse(high, speaker_match, contextual)

    assert r_high.risk_score >= r_low.risk_score - 1e-9  # float tolerance


@given(
    base_score=st.floats(min_value=0.0, max_value=0.8),
    increase=st.floats(min_value=0.01, max_value=0.2),
    confidence=st.floats(min_value=0.5, max_value=1.0),
    contextual=signal_strategy(),
)
@settings(max_examples=200)
def test_monotonic_in_speaker_mismatch_score(base_score, increase, confidence, contextual):
    synthesis = unavailable_signal
    low = Signal(score=base_score, confidence=confidence, available=True)
    high = Signal(score=min(1.0, base_score + increase), confidence=confidence, available=True)

    r_low = fuse(synthesis, low, contextual)
    r_high = fuse(synthesis, high, contextual)

    assert r_high.risk_score >= r_low.risk_score - 1e-9


# ---------------------------------------------------------------------
# Property: an unavailable signal is never silently treated as "clean."
# Missing evidence must not systematically pull risk toward zero.
# ---------------------------------------------------------------------
def test_missing_speaker_match_does_not_fake_safety():
    synthesis = Signal(score=0.9, confidence=0.95, available=True)
    speaker_match_missing = unavailable_signal
    speaker_match_clean = Signal(score=0.0, confidence=0.95, available=True)
    contextual = unavailable_signal

    r_missing = fuse(synthesis, speaker_match_missing, contextual)
    r_clean = fuse(synthesis, speaker_match_clean, contextual)

    # Missing a second opinion should not score LOWER than actively
    # confirming the second opinion is clean -- if anything it should be
    # at least as cautious, since "not checked" != "checked and fine."
    assert r_missing.risk_score >= r_clean.risk_score - 1e-9


# ---------------------------------------------------------------------
# Fail-safe: total absence of acoustic evidence must not resolve to
# "no risk" -- see DESIGN.md 4.7 on never failing open.
# ---------------------------------------------------------------------
def test_total_signal_failure_does_not_fail_open():
    contextual = unavailable_signal
    result = fuse(unavailable_signal, unavailable_signal, contextual)
    assert result.degraded is True
    assert result.risk_score > 0.0  # never silently "safe"
    assert "RECOMMEND" in result.actions[0] or "ESCALATION" in " ".join(result.actions)


# ---------------------------------------------------------------------
# Explainability: high-risk output must always include a non-trivial
# explanation string -- a bare number is not acceptable for a system
# whose output can trigger blocking a financial transaction.
# ---------------------------------------------------------------------
def test_high_risk_always_explained():
    synthesis = Signal(score=0.95, confidence=0.9, available=True)
    speaker_match = Signal(score=0.9, confidence=0.9, available=True)
    contextual = Signal(score=0.8, confidence=0.9, available=True)

    result = fuse(synthesis, speaker_match, contextual)
    assert result.risk_score >= HIGH_RISK_ACTION_THRESHOLD
    assert len(result.explanation) > 20
    assert "high risk" in result.explanation


# ---------------------------------------------------------------------
# Contextual signal alone (clean acoustics) should raise risk only
# moderately, never to "high" -- see design decision 3 in fusion.py.
# ---------------------------------------------------------------------
def test_context_alone_cannot_drive_high_risk():
    synthesis = Signal(score=0.0, confidence=0.9, available=True)
    speaker_match = Signal(score=0.0, confidence=0.9, available=True)
    contextual = Signal(score=1.0, confidence=1.0, available=True)

    result = fuse(synthesis, speaker_match, contextual)
    assert result.risk_score < HIGH_RISK_ACTION_THRESHOLD
