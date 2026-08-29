"""
Content-risk scoring via Groq LLM.

Evaluates whether a conversation transcript contains scam indicators
(OTP requests, fund transfer demands, urgent credential disclosure,
authority-pressure language) and returns a structured risk score.

DESIGN INVARIANTS:
  - JSON output is ENFORCED via Groq's response_format + strict parsing.
  - On ANY failure (network, parse, timeout) → returns available=false,
    following the existing fail-safe pattern (never fake a safe score).
  - Groq API key is read from GROQ_API_KEY environment variable
    (server-side only, never embedded in client app binary).
  - Transcript is passed as-is (PII redaction is the caller's
    responsibility — the Android app already redacts before sending).
"""

import json
import logging
import os
from dataclasses import dataclass
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"
GROQ_TIMEOUT_S = 6.0

SYSTEM_PROMPT = """You are a financial fraud content analyzer for phone calls in India.
Analyze the transcript and determine if the caller is attempting:
1. Fund transfer / money demand
2. OTP or credential disclosure
3. Authority impersonation with urgency (police, CBI, TRAI, RBI)
4. Social engineering pressure tactics

Return ONLY a JSON object, no other text:
{"content_risk_score": <float 0.0-1.0>, "reason": "<short string explaining why>"}

Rules:
- 0.0-0.2: Normal conversation, no risk indicators
- 0.3-0.5: Mild concern (mentions of money/accounts but no pressure)
- 0.6-0.8: Clear scam indicators (OTP request, fake authority claim)
- 0.9-1.0: Active scam in progress (urgent fund transfer + authority pressure)
- If the transcript is too short or unclear, return score 0.0 with reason "insufficient content"
"""


@dataclass(frozen=True)
class ContentRiskResult:
    """Result of content-risk analysis."""
    score: float       # 0.0-1.0
    confidence: float  # 0.0-1.0
    available: bool
    detail: str


def _failsafe(reason: str) -> ContentRiskResult:
    """Return an unavailable signal — never a fake safe score."""
    return ContentRiskResult(
        score=0.0,
        confidence=0.0,
        available=False,
        detail=reason,
    )


async def assess_content_risk(
    transcript: str,
    context: str = "",
) -> ContentRiskResult:
    """
    Call Groq LLM to assess content risk of a conversation transcript.

    Returns ContentRiskResult with available=true on success,
    available=false on any failure (fail-safe).
    """
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        logger.warning("GROQ_API_KEY not set — content risk unavailable")
        return _failsafe("GROQ_API_KEY not configured")

    if not transcript or len(transcript.strip()) < 5:
        return _failsafe("transcript too short for analysis")

    user_content = f"--- TRANSCRIPT ---\n{transcript}\n--- END ---"
    if context:
        user_content += f"\nContext: {context}"

    request_body = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
    }

    try:
        async with httpx.AsyncClient(timeout=GROQ_TIMEOUT_S) as client:
            resp = await client.post(
                GROQ_API_URL,
                json=request_body,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
            )
            resp.raise_for_status()
    except Exception as e:
        logger.warning("Groq API call failed: %s", e)
        return _failsafe(f"Groq API error: {type(e).__name__}")

    # Parse Groq response → extract JSON content
    try:
        resp_json = resp.json()
        content = resp_json["choices"][0]["message"]["content"]
        parsed = json.loads(content)
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        logger.warning("Groq response parse failed: %s", e)
        return _failsafe(f"Groq response parse error: {type(e).__name__}")

    # Validate the expected fields
    try:
        score = float(parsed["content_risk_score"])
        reason = str(parsed.get("reason", ""))
    except (KeyError, TypeError, ValueError) as e:
        logger.warning("Groq JSON validation failed: %s — raw: %s", e, parsed)
        return _failsafe(f"Groq JSON validation error: {type(e).__name__}")

    # Clamp score to [0.0, 1.0]
    score = max(0.0, min(1.0, score))

    return ContentRiskResult(
        score=score,
        confidence=0.85,  # LLM-based signal — high but not perfect confidence
        available=True,
        detail=reason,
    )
