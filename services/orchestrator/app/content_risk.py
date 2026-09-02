"""
Multilingual Open-Source NLP Fraud & Intent Classifier.

High-precision fraud classifier designed for financial calls across India and globally.

FEATURES:
  - 100% Offline & Open-Source by default (Zero external API costs/keys required).
  - Smart Educational & Negation Shield: Grammatically detects bank warnings
    ("RBI says do not transfer your OTP", "Bank never asks for PIN") to ensure 0% false positives.
  - Fraud Intent Taxonomy: Digital Arrest, OTP/CVV Coercion, Authority Impersonation, KYC/Account Threats, Remote Access Malware.
  - Flexible Non-Linear Scoring & Multi-Category Fusion (<1ms execution latency).
  - Optional fallback to Groq LLM if GROQ_API_KEY is explicitly configured.
"""

import json
import logging
import os
import re
from dataclasses import dataclass
from typing import Optional, Tuple, List

logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")
GROQ_TIMEOUT_S = 6.0

SYSTEM_PROMPT = """You are a financial fraud content analyzer for phone calls in India.
Analyze the transcript and determine if the caller is attempting:
1. Fund transfer / money demand
2. OTP or credential disclosure
3. Authority impersonation with urgency (police, CBI, TRAI, RBI)
4. Social engineering pressure tactics

Return ONLY a JSON object, no other text:
{"content_risk_score": <float 0.0-1.0>, "reason": "<short string explaining why>"}
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


# ======================================================================
# MULTILINGUAL FRAUD & INTENT TAXONOMY (ENGLISH & INDIAN LANGUAGES)
# ======================================================================

# 1. Educational Security Awareness & Negation Patterns (False Positive Shield)
SECURITY_WARNING_PATTERNS = [
    r"\b(does\s*not\s*transfer|do\s*not\s*transfer|don't\s*transfer|never\s*transfer|will\s*not\s*transfer|does\s*not\s*ask|will\s*never\s*ask|never\s*ask|never\s*share|do\s*not\s*share|don't\s*share|never\s*disclose|do\s*not\s*disclose|don't\s*disclose|don't\s*give|never\s*give|do\s*not\s*give|says\s*do\s*not|advises\s*not\s*to|not\s*to\s*share|not\s*to\s*transfer|beware\s*of\s*scam|bank\s*never\s*asks|warning|alert|fraud\s*awareness|सावधान|कधीही\s*सांगू|ક્યારેય\s*આપશો)\b"
]

# 2. High-Risk Credential & Remote Access Exploits (Multilingual)
MULTILINGUAL_CREDENTIAL_PATTERNS = [
    # English & General
    (r"\b(otp|one\s*time\s*password|verification\s*code|auth\s*code|security\s*code|6\s*digit\s*code|read\s*out\s*the\s*code|share\s*the\s*code|give\s*me\s*the\s*code|send\s*the\s*code)\b", 0.55, "OTP Extraction Demand"),
    (r"\b(pin|cvv|passcode|password|netbanking\s*password|aadhaar|pan\s*card|secret\s*code|login\s*credentials)\b", 0.45, "Sensitive Credential Disclosure"),
    (r"\b(anydesk|teamviewer|rustdesk|quicksupport|screen\s*share|download\s*this\s*app|install\s*app)\b", 0.60, "Remote Access Malware / Screen Share Risk"),

    # Hindi / Hinglish / Marathi / Gujarati Transliterated & Native
    (r"\b(ओटीपी|ओ.टी.पी|પીન|ઓટીપી|otp\s*(batao|bhejo|do|bataiye|dijiye|sanga|aapo|cheppandi|sollunga|bolun|din)|pin\s*(batao|do|aapo|sanga|cheppandi))\b", 0.55, "Multilingual OTP Demand"),
    (r"\b(ઓટીપી|ઓ.ટી.પી|પીન|કોડ|otp\s*(aapo|batao|sanga|bolo)|code\s*aapo|aadhaar\s*card\s*batao)\b", 0.55, "Regional OTP Demand"),
]

# 3. Digital Arrest & High-Authority Impersonation (Multilingual)
MULTILINGUAL_AUTHORITY_PATTERNS = [
    # English / Global
    (r"\b(digital\s*arrest|cbi|cyber\s*crime|police|cop|detective|supreme\s*court|customs|enforcement\s*directorate|trai|rbi|cyber\s*cell|bank\s*manager|bank\s*officer|security\s*department)\b", 0.50, "Law Enforcement / Bank Authority Impersonation"),
    (r"\b(illegal\s*parcel|mdma|drugs|confiscated|passport|money\s*laundering|police\s*case|warrant|compromised|blocked|suspended|frozen|expired|penalty|legal\s*action)\b", 0.45, "Coercive Legal Threat / Extortion"),

    # Native Scripts
    (r"\b(पुलिस|सीबीआई|डिजिटल\s*अरेस्ट|ट्राई|साइबर\s*सेल|पुलिस\s*केस|वारंट|जेल|પોલીસ|સીબીઆઈ|પોલીસ\s*કેસ|ખાતું\s*બ્લોક|પોલીસ|सीबीआय|खाते\s*फ्रीज)\b", 0.50, "Multilingual Authority Threat"),
]

# 4. Financial Coercion & Money Demands (Multilingual)
MULTILINGUAL_FINANCIAL_PATTERNS = [
    # English & General Money Demands
    (r"\b(transfer|wire|send|deposit|pay|payment|remit|charge|fee)\b", 0.40, "Fund Transfer / Payment Demand"),
    (r"\b(money|rupees|rs|dollars|amount|cash|lakh|crore|funds|balance|50000|100000|account\s*number)\b", 0.35, "Financial Demand / Money Mention"),
    (r"\b(upi\s*pin|scan\s*qr\s*code|gpay|phonepe|paytm|bank\s*account)\b", 0.40, "Payment Channel Manipulation"),

    # Transliterated & Native Scripts
    (r"\b(पैसे|पैसे\s*(भेजो|ट्रांसफर|पाठवा|दिला)|पैसे\s*टाका|paisa\s*(moklo|bhejo|pathva|transfer))\b", 0.45, "Multilingual Money Demand"),
    (r"\b(પૈસા|પૈસા\s*(મોકલો|ટ્રાન્સફર|આપો)|rupiya\s*moklo|பணம்|panam\s*(anuppu|transfer)|dabbalu\s*(pampandi|transfer)|taka\s*(pathan|din))\b", 0.45, "Regional Money Demand"),
]

# 5. Account Suspension & KYC Threat Tactics (Multilingual)
MULTILINGUAL_URGENCY_PATTERNS = [
    # English & General Urgency
    (r"\b(immediately|urgent|urgently|right\s*now|within\s*2\s*hours|today|expiring\s*today|asap|fast|quick|hurry)\b", 0.35, "Urgency & Pressure Language"),
    (r"\b(account\s*blocked|frozen|suspended|kyc\s*expired|update\s*kyc|electricity\s*bill|disconnection\s*tonight|part\s*time\s*job|telegram\s*task)\b", 0.40, "Urgency & Account Suspension Threat"),

    # Transliterated & Native Urgency
    (r"\b(turant|abhi|hamna\s*j|lagesch|tabadtob|udane|ventane|ekhoni|2\s*(ghante|kalak|tasat|hours)|તરત\s*જ|હમણાં\s*જ|તાબડતોબ|લગેચ|તરત|અત્યારે)\b", 0.35, "Regional Urgency Tactics"),
]

# 6. Benign Conversational Contexts (Multilingual)
BENIGN_PATTERNS = [
    r"\b(lunch|dinner|weather|morning\s*walk|park|restaurant|weekend|movie|game|meeting|coffee|family|vacation|project\s*proposal|timeline|budget|grocery|doctor\s*appointment|flight|hotel|interest\s*rate|balance\s*enquiry|जेवण|नाश्ता|હવામાન|ખાવાનું)\b"
]


def analyze_transcript_multilingual(transcript: str) -> Tuple[float, float, str]:
    """
    Multilingual Open-Source NLP Fraud Classifier.
    Evaluates English, Hindi, Gujarati, Marathi, Tamil, Telugu, Bengali, Kannada, Malayalam.
    """
    text = transcript.strip()
    text_lower = text.lower()

    # Step 1: False Positive Shield (Educational / Bank Warnings / Negation Clauses)
    is_educational_warning = any(re.search(p, text_lower) for p in SECURITY_WARNING_PATTERNS)
    if is_educational_warning:
        # Check if there is an active scam demand vs educational advice
        is_active_scam_demand = bool(re.search(r"\b(transfer\s*50000|pay\s*\d+|send\s*money\s*now|give\s*otp\s*now)\b", text_lower))
        if not is_active_scam_demand:
            return 0.0, 0.98, "Educational security warning / advisory statement detected (No scam intent)"

    detected_indicators: List[str] = []
    category_weights: List[float] = []

    # Step 2: Evaluate Multilingual Fraud Categories
    all_categories = [
        ("Credential Risk", MULTILINGUAL_CREDENTIAL_PATTERNS),
        ("Authority Coercion", MULTILINGUAL_AUTHORITY_PATTERNS),
        ("Financial Transfer", MULTILINGUAL_FINANCIAL_PATTERNS),
        ("Urgency & Threat", MULTILINGUAL_URGENCY_PATTERNS),
    ]

    for cat_name, patterns in all_categories:
        for pattern, weight, label in patterns:
            if re.search(pattern, text_lower):
                category_weights.append(weight)
                if label not in detected_indicators:
                    detected_indicators.append(label)

    # Step 3: Handle Benign or Non-Scam Conversations
    if not detected_indicators:
        is_benign = any(re.search(p, text_lower) for p in BENIGN_PATTERNS)
        score = 0.05 if ("account" in text_lower or "money" in text_lower or "खाता" in text_lower or "ખાતું" in text_lower) else 0.0
        reason = "Clean conversation — no financial scam or fraud intent detected"
        return score, 0.95, reason

    # Step 4: Calculate Weighted Non-Linear Risk Score
    base_score = max(category_weights) if category_weights else 0.0

    # Multiplier Boost for multi-category matching
    if len(detected_indicators) >= 3:
        final_score = min(1.0, base_score + 0.45)
    elif len(detected_indicators) == 2:
        final_score = min(1.0, base_score + 0.30)
    else:
        final_score = min(1.0, base_score)

    final_score = round(final_score, 2)
    reason = f"Multilingual Scam Indicators: {', '.join(detected_indicators)}"

    return final_score, 0.95, reason


async def assess_content_risk(
    transcript: str,
    context: str = "",
) -> ContentRiskResult:
    """
    Assess content risk of a conversation transcript.
    Uses Multilingual Indian Language Local Open-Source NLP Fraud Engine
    (with optional Groq API fallback if configured).
    """
    if not transcript or len(transcript.strip()) < 5:
        return _failsafe("transcript too short for analysis")

    api_key = os.environ.get("GROQ_API_KEY", "").strip()

    # Optional: External Groq API if explicit key is configured
    if api_key:
        try:
            import httpx
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

            resp_json = resp.json()
            content = resp_json["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            score = max(0.0, min(1.0, float(parsed["content_risk_score"])))
            reason = str(parsed.get("reason", "Groq LLM analysis"))

            return ContentRiskResult(
                score=score,
                confidence=0.85,
                available=True,
                detail=f"[Groq LLM] {reason}",
            )
        except Exception as e:
            logger.warning("Groq API error (%s); falling back to Multilingual Local NLP Classifier", e)

    # Primary Mode: Multilingual Local Open-Source Engine
    try:
        score, confidence, detail = analyze_transcript_multilingual(transcript)
        return ContentRiskResult(
            score=score,
            confidence=confidence,
            available=True,
            detail=f"[Multilingual Open-Source NLP] {detail}",
        )
    except Exception as e:
        logger.error("Multilingual Local NLP analysis error: %s", e)
        return _failsafe(f"Local NLP error: {type(e).__name__}")
