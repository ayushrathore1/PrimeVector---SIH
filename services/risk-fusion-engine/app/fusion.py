"""
Risk fusion logic for the voice-integrity platform.

This module is deliberately written by hand, not generated, because it is
the component a bank's compliance team and (eventually) a regulator will
audit. Every design decision here is a business/liability decision, not
just an engineering one, and is documented inline.

Design decisions (see docs/DESIGN.md for full rationale):

1. Determinism: same inputs -> same output, always. No randomness, no
   hidden state, no wall-clock dependence in the scoring itself.
2. Noisy-OR combination for the two acoustic signals (synthesis detection,
   speaker mismatch): either signal alone being highly suspicious is
   sufficient to raise risk. We deliberately do NOT average them, because
   averaging would let a strong detection get diluted by the other
   detector's uncertainty -- and these two signals are testing genuinely
   different things (is this audio synthetic at all vs. does this voice
   match who they claim to be), so they should not cancel each other out.
3. Contextual signal acts as a MULTIPLIER on top of the acoustic evidence,
   never as a standalone driver of high risk. A suspicious transaction
   context with clean acoustic signals should nudge risk up moderately,
   not spike it -- we should not be confidently accusing someone of voice
   fraud based on metadata alone.
4. Missing/unavailable signals (e.g. no enrollment -> no speaker-match
   signal) degrade gracefully rather than being treated as "0 risk" --
   an unavailable signal is evidence of nothing, not evidence of safety.
5. The engine outputs a human-readable explanation string built from which
   signals actually contributed. A bare number is not acceptable output
   for a system whose decisions can block a financial transaction.
"""

from dataclasses import dataclass
from typing import Optional


# Tunable thresholds are named constants, not embedded magic numbers, so
# they can be surfaced to the policy engine / audited independently of
# the fusion math itself.
CONTEXTUAL_MULTIPLIER_MIN = 0.85   # contextual signal can reduce acoustic-driven
                                     # risk by at most this fraction ...
CONTEXTUAL_MULTIPLIER_MAX = 1.35   # ... or amplify it by at most this fraction.
                                     # Bounded deliberately: metadata should never
                                     # be able to fully override or fully suppress
                                     # what the acoustic evidence says.

HIGH_RISK_ACTION_THRESHOLD = 0.70
MODERATE_RISK_ACTION_THRESHOLD = 0.40


@dataclass(frozen=True)
class Signal:
    """One independent evidence signal. Mirrors proto/risk_assessment.proto RiskSignal."""
    score: float           # 0.0-1.0, higher = more suspicious
    confidence: float      # 0.0-1.0, model's own confidence in `score`
    available: bool = True
    detail: str = ""

    def __post_init__(self):
        if self.available:
            if not (0.0 <= self.score <= 1.0):
                raise ValueError(f"score out of bounds: {self.score}")
            if not (0.0 <= self.confidence <= 1.0):
                raise ValueError(f"confidence out of bounds: {self.confidence}")


@dataclass(frozen=True)
class FusionResult:
    risk_score: float
    confidence: float
    actions: list
    explanation: str
    degraded: bool


def _noisy_or(signals: list) -> float:
    """
    Combine independent 'suspicious' probabilities such that the combined
    probability of 'at least one real threat indicator fired' is returned.

    P(not suspicious at all) = product over signals of (1 - score)
    P(suspicious)            = 1 - that product

    This is the standard noisy-OR combination for independent evidence.
    Unavailable signals are excluded from the product entirely (see
    module docstring point 4) rather than treated as score=0, which would
    incorrectly count "we don't know" as "we checked and it's clean."
    """
    available = [s for s in signals if s.available]
    if not available:
        return None  # caller must handle: no acoustic evidence at all
    p_clean = 1.0
    for s in available:
        p_clean *= (1.0 - s.score)
    return 1.0 - p_clean


def _contextual_multiplier(contextual: Signal) -> float:
    """
    Maps a contextual risk signal onto a bounded multiplier. Bounded per
    design decision 3: context nudges, it does not dominate.
    """
    if not contextual.available:
        return 1.0
    span = CONTEXTUAL_MULTIPLIER_MAX - CONTEXTUAL_MULTIPLIER_MIN
    return CONTEXTUAL_MULTIPLIER_MIN + contextual.score * span


def _actions_for(risk_score: float, enrollment_missing: bool) -> list:
    actions = []
    if enrollment_missing and risk_score >= MODERATE_RISK_ACTION_THRESHOLD:
        # No baseline voiceprint to compare against AND already-elevated
        # risk from other signals: recommend verification even though we
        # could not check speaker identity directly.
        actions.append("RECOMMEND_CALLBACK_VERIFICATION")
    if risk_score >= HIGH_RISK_ACTION_THRESHOLD:
        actions.append("RECOMMEND_CALLBACK_VERIFICATION")
        actions.append("RECOMMEND_SUPERVISOR_ESCALATION")
    elif risk_score >= MODERATE_RISK_ACTION_THRESHOLD:
        actions.append("RECOMMEND_MFA_STEP_UP")
    else:
        actions.append("PROCEED")
    # Dedup while preserving order (a set() would not preserve order,
    # and order matters for the UI showing "primary" vs "secondary" action).
    seen = set()
    deduped = []
    for a in actions:
        if a not in seen:
            seen.add(a)
            deduped.append(a)
    return deduped


def _explain(synthesis: Signal, speaker_match: Signal, contextual: Signal,
             risk_score: float, degraded: bool) -> str:
    parts = []
    if synthesis.available and synthesis.score >= 0.5:
        parts.append(f"synthesis artifacts detected (score={synthesis.score:.2f})")
    elif synthesis.available:
        parts.append(f"no significant synthesis artifacts (score={synthesis.score:.2f})")
    else:
        parts.append("synthesis check unavailable")

    if speaker_match.available and speaker_match.score >= 0.5:
        parts.append(f"voice does not match enrolled sample (mismatch={speaker_match.score:.2f})")
    elif speaker_match.available:
        parts.append(f"voice matches enrolled sample (mismatch={speaker_match.score:.2f})")
    else:
        parts.append("no enrolled voiceprint on file to compare against")

    if contextual.available and contextual.score >= 0.5:
        parts.append(f"transaction context is elevated risk (score={contextual.score:.2f})")

    prefix = "DEGRADED (partial signal) — " if degraded else ""
    level = "high" if risk_score >= HIGH_RISK_ACTION_THRESHOLD else (
        "moderate" if risk_score >= MODERATE_RISK_ACTION_THRESHOLD else "low")
    return f"{prefix}{level} risk ({risk_score:.2f}): " + "; ".join(parts)


def fuse(synthesis: Signal, speaker_match: Signal, contextual: Signal) -> FusionResult:
    """
    Deterministic risk fusion. Given the same three signals, always
    returns the same result -- this is a hard requirement (see module
    docstring), not an implementation convenience.
    """
    acoustic_risk = _noisy_or([synthesis, speaker_match])
    degraded = acoustic_risk is None

    if degraded:
        # No acoustic evidence available at all (e.g. total feature-extraction
        # failure upstream). We do NOT default to a low score here -- that
        # would be "fail open," which docs/DESIGN.md 4.7 explicitly forbids.
        # We surface an explicit unknown/degraded state instead and let the
        # caller's fail-safe policy decide (typically: recommend manual
        # verification, since we cannot vouch for the call at all).
        risk_score = MODERATE_RISK_ACTION_THRESHOLD  # treated as "at least caution"
        confidence = 0.0
    else:
        multiplier = _contextual_multiplier(contextual)
        risk_score = min(1.0, acoustic_risk * multiplier)
        # Fused confidence: we are only as confident as our least confident
        # *available* acoustic signal -- a high risk score built on a
        # low-confidence detector should not be presented as equally
        # trustworthy as one built on two high-confidence detectors.
        available_acoustic = [s for s in (synthesis, speaker_match) if s.available]
        confidence = min(s.confidence for s in available_acoustic)

    enrollment_missing = not speaker_match.available
    actions = _actions_for(risk_score, enrollment_missing)
    explanation = _explain(synthesis, speaker_match, contextual, risk_score, degraded)

    return FusionResult(
        risk_score=risk_score,
        confidence=confidence,
        actions=actions,
        explanation=explanation,
        degraded=degraded,
    )
