# SIH Technical Q&A — Satya Voice Integrity Platform
## Prime Vector — Comprehensive Preparation Guide

> This document covers **every aspect** of the Satya platform: architecture, algorithms, security, compliance, deployment, scalability, and design trade-offs. Questions range from high-level concept to deep code-level detail.

---

## SECTION 1: Problem Statement & Motivation

### Q1. What problem does Satya solve?
**A.** Satya is a real-time voice integrity and impersonation prevention platform. AI voice cloning has become so advanced that a 5-second audio snippet from social media can generate a voice clone indistinguishable to human ears. Scammers use this to impersonate bank officers, executives, and family members to authorize fraudulent wire transfers, extract OTPs, and reset credentials. Satya detects these attacks in real-time during live phone calls by analyzing acoustic, biometric, and conversational signals that humans cannot perceive.

### Q2. Why can't existing solutions solve this?
**A.** Existing solutions have three critical gaps:
1. **Single-signal fragility**: Most tools use either voice biometrics OR deepfake detection — never both. A single-signal system can be fooled by an attacker who targets that specific signal.
2. **Fail-open defaults**: Many systems treat errors or missing data as "safe" (score = 0.0), silently passing fraudulent calls through when a service is down.
3. **Black-box decisions**: Existing solutions return a single opaque number without explaining which signals contributed, making regulatory audit and human override impossible.

Satya addresses all three: multi-signal fusion, fail-safe-by-default, and human-readable explanations for every decision.

### Q3. Who are the target users?
**A.** Four verticals:
| Segment | Use Case |
|---|---|
| **Banks & Financial Institutions** | Prevent fraudulent wire transfers, unauthorized password resets, high-value transaction approvals over phone |
| **Enterprise Executives** | Protect CXOs from CEO-fraud / BEC (Business Email Compromise) voice attacks |
| **Telecom / Call Centers** | Flag suspicious callers before agents access sensitive accounts |
| **Government & Defense** | Verify official identities during critical voice communications |

### Q4. What is the SIH problem statement alignment?
**A.** The project aligns with SIH themes on **Cybersecurity & Digital Trust**. Specifically, it addresses the intersection of AI-generated content (deepfakes), digital identity verification, and real-time fraud prevention in India's financial infrastructure. The platform is designed for the Indian context — supporting multilingual accent clusters (Hindi, Tamil, Telugu, Bengali) and addressing UPI/NEFT scam patterns common in India.

---

## SECTION 2: Architecture & System Design

### Q5. Describe the overall architecture.
**A.** Satya uses an **event-driven microservice architecture** with 8 independent services organized into 4 tiers:

| Tier | Services | Responsibility |
|---|---|---|
| **Ingress** | Ingestion Gateway (Go/gRPC, :50051) | High-throughput streaming, rate limiting, backpressure |
| **Feature & Detection** | Feature Extraction (:8001), Spoof Detection (:8002), Enrollment (:8003) | Audio analysis, deepfake detection, voiceprint matching |
| **Decision** | Risk Fusion Engine (:8000), Policy Engine (:8004) | Deterministic risk scoring, tenant-specific policy rules |
| **Notification** | Alerting Service (:8005) | Multi-channel alert dispatch with audit trails |

The **Orchestrator** (:8080) coordinates the end-to-end 5-step pipeline across all services.

### Q6. Why microservices instead of a monolith?
**A.** Three reasons:
1. **Fault isolation**: If the spoof detection model crashes, enrollment verification and content analysis still work. A monolith would take down everything.
2. **Independent scaling**: The feature extraction service is CPU-heavy (mel spectrogram computation) while the policy engine is pure logic. They have vastly different scaling profiles.
3. **Compliance boundaries**: The risk-fusion-engine contains regulator-audited math. Isolating it means compliance teams can audit and freeze that service independently without blocking development of other features.

### Q7. Why is the Ingestion Gateway written in Go while everything else is Python?
**A.** The ingestion gateway handles **50,000 concurrent gRPC audio streams** with per-tenant rate limiting and backpressure flow control. Go's goroutine-based concurrency model handles this naturally with minimal memory overhead (~4KB per goroutine vs ~8MB per Python thread). The gateway is a stateless I/O multiplexer — no ML inference, no complex business logic — so Go's strengths in concurrent networking are a perfect fit. The downstream Python services handle the ML and business logic where Python's ecosystem (PyTorch, librosa, FastAPI) is stronger.

### Q8. Explain the 5-step orchestration pipeline.
**A.**
```
Step 1: Feature Extraction
    POST /v1/extract → log-mel spectrogram (80 bands) + 192-dim speaker embedding

Step 2: Parallel Detection (asyncio.gather)
    2a. POST /v1/detect → synthesis_signal (is this AI-generated?)
    2b. GET  /status    → speaker_match_signal (does voice match enrolled voiceprint?)
    2c. Local Ollama LLM → content_risk_signal (is the transcript a scam script?)

Step 3: Risk Fusion
    POST /v1/assess → Noisy-OR fusion of all signals → fused risk_score

Step 4: Policy Evaluation
    POST /v1/evaluate → Apply tenant-specific thresholds → final_action

Step 5: Alert Dispatch
    POST /v1/events → Multi-channel notification + SHA-256 hashed audit log
```

Steps 2a, 2b, and 2c execute **in parallel** using Python's `asyncio.gather()`, reducing total latency by ~60% compared to sequential execution.

### Q9. What happens if one downstream service fails during the pipeline?
**A.** The system **never fails open**. Each service failure is handled individually:
- **Feature extraction fails** → Entire pipeline returns `degraded: true` with `RECOMMEND_CALLBACK_VERIFICATION`. No signals can be computed without features.
- **Spoof detection fails** → `synthesis_signal.available = false`. Fusion engine excludes it from Noisy-OR (it does NOT treat missing as score=0.0).
- **Enrollment unavailable** → `speaker_match_signal.available = false`. If combined with elevated risk from other signals, the system recommends callback verification even though identity couldn't be checked.
- **Risk fusion engine fails** → Pipeline returns degraded with the most cautious recommendation.
- **Policy engine fails** → Fusion engine's own action recommendations are used directly (degraded mode).
- **Alerting fails** → Non-blocking. Pipeline still returns the risk assessment; the alert is logged as failed.

### Q10. How do services communicate?
**A.** Two protocols:
1. **gRPC** (Protocol Buffers) — Used at the ingestion edge for streaming audio chunks. The `.proto` contract defines `RiskSignal`, `RiskAssessmentRequest/Response`, and `RecommendedAction` enums.
2. **HTTP/JSON** (REST) — Used between all Python microservices via FastAPI. The orchestrator uses `httpx.AsyncClient` for non-blocking downstream calls.

All services are connected via a Docker `bridge` network (`voice-integrity`). Service discovery uses Docker Compose DNS names (e.g., `http://risk-fusion-engine:8000`).

---

## SECTION 3: Algorithms & Mathematics

### Q11. Explain the Noisy-OR fusion formula. Why not simple averaging?
**A.** The core fusion uses **Noisy-OR probability combination**:

$$P(\text{suspicious}) = 1 - \prod_{s \in \text{available}} (1 - s.\text{score})$$

**Why not averaging?** Consider: synthesis detection returns 0.95 (very suspicious) and speaker match returns 0.10 (looks fine).
- **Average**: (0.95 + 0.10) / 2 = **0.525** — moderate risk. The strong detection is diluted!
- **Noisy-OR**: 1 - (1-0.95)(1-0.10) = 1 - (0.05)(0.90) = **0.955** — high risk preserved.

Noisy-OR treats each signal as an **independent failure mode**. If ANY one signal fires strongly, the combined probability stays high. This is correct because synthesis detection and speaker verification test genuinely different things — a call can be AI-generated (high synthesis score) while coincidentally matching a voiceprint (low speaker mismatch). Averaging would incorrectly suppress the synthesis alarm.

### Q12. How does the contextual multiplier work?
**A.** The contextual signal (transaction amount, device risk, call metadata) acts as a **bounded multiplier** on acoustic evidence:

$$\text{multiplier} = 0.85 + s_{\text{context}} \times (1.35 - 0.85)$$
$$\text{fused\_score} = \min(1.0, \; P(\text{suspicious}) \times \text{multiplier})$$

The bounds **[0.85, 1.35]** are deliberate:
- Context can **reduce** acoustic risk by at most 15% (a low-risk transaction context slightly lowers concern)
- Context can **amplify** acoustic risk by at most 35% (a ₹50 lakh transfer with a new device increases concern)
- **Context alone can NEVER drive risk above 0.40** (MODERATE threshold) if acoustic evidence is clean. This prevents false positives based purely on metadata like "the caller is using a new phone."

### Q13. What is the content risk signal and how is it generated?
**A.** The content risk signal uses **LLM-based transcript analysis** via a local Ollama LLM (qwen3:4b). The orchestrator sends the call transcript to the locally-running language model with a structured system prompt that evaluates four scam indicators:
1. Fund transfer / money demands
2. OTP or credential disclosure requests
3. Authority impersonation with urgency (fake police/CBI/TRAI/RBI officers)
4. Social engineering pressure tactics

The LLM returns a structured JSON `{"content_risk_score": 0.0-1.0, "reason": "..."}` via Ollama's JSON schema enforcement. All inference runs 100% on-device — zero data leaves the user's machine.

**Fail-safe**: If Ollama is unreachable, times out, or returns malformed JSON, the system falls back to the local multilingual NLP classifier (regex/intent-based). If that also fails, the signal returns `available: false` — it never fakes a safe score.

### Q14. How is fused confidence calculated?
**A.** Fused confidence = **minimum confidence** among all available evidence signals:

```python
confidence = min(s.confidence for s in available_evidence)
```

This means a high risk score built on a low-confidence detector is presented as less trustworthy than one built on two high-confidence detectors. The system is only as confident as its weakest contributing signal.

### Q15. How does the spoof detection confidence formula work?
**A.** The spoof detector converts raw model logits to scores using sigmoid + calibrated confidence:

$$\text{score} = \sigma(z) = \frac{1}{1 + e^{-z}}$$
$$\text{confidence} = 2 \cdot |\text{score} - 0.5|$$

The confidence formula captures the model's certainty: a score of 0.5 (completely uncertain) yields confidence 0.0, while scores near 0.0 or 1.0 (highly certain either way) yield confidence near 1.0.

### Q16. What features does the Feature Extraction service produce?
**A.** Two outputs:
1. **Log-Mel Spectrogram**: 80 mel frequency bands, 10ms hop length, 25ms Hamming window. Captures the spectral energy distribution of speech — AI-synthesized audio has subtle artifacts in high-frequency mel bands that natural speech doesn't.
2. **Speaker Embedding**: 192-dimensional vector via d-vector / ResNet architecture. This is a compressed mathematical representation of "who" is speaking, invariant to what they're saying.

**Critical privacy guarantee**: Raw audio bytes are decoded from Base64 into RAM, features are extracted, and the audio is immediately garbage-collected. No `audio_bytes` field exists in any response model.

---

## SECTION 4: Security, Privacy & Compliance

### Q17. What is the "never fail open" invariant?
**A.** This is the platform's #1 safety rule. When any component fails, times out, or returns unexpected data:
- Missing signals are marked `available: false`, NOT treated as `score = 0.0`
- The pipeline returns `degraded: true` with a cautious recommendation (`RECOMMEND_CALLBACK_VERIFICATION`)
- The Noisy-OR formula **excludes** unavailable signals entirely rather than counting them as "safe"

The alternative — "failing open" — would mean a service outage silently passes all calls as safe, which is unacceptable in a financial fraud prevention system.

### Q18. How is audio privacy guaranteed (zero retention)?
**A.** Multiple enforcement layers:
1. **No storage fields**: Pydantic response models contain no `audio_bytes` or `raw_audio` fields. It's structurally impossible to return audio in an API response.
2. **In-memory processing**: Base64 audio is decoded to a NumPy array, features are extracted, and the array is dereferenced. Python's garbage collector reclaims the memory.
3. **No disk I/O**: No `open()`, `write()`, or database INSERT for audio data anywhere in the codebase.
4. **Audit-safe**: The orchestrator explicitly comments `# Audio base64 reference is no longer needed after this point.`

### Q19. How does the auto-block safety gate work?
**A.** `auto_block_enabled` defaults to `False` for every tenant. The policy evaluation logic:

```python
if config.auto_block_enabled and risk_score >= config.block_threshold:
    return "BLOCK_PENDING_VERIFICATION"
```

If `auto_block_enabled == False`, this branch is **unreachable** — even a risk score of 1.0 returns `RECOMMEND_SUPERVISOR_ESCALATION` (a recommendation to a human), never an automatic block. This is a liability gate: a tenant must explicitly opt into automated blocking, accepting responsibility for false positives.

### Q20. How are audit logs protected?
**A.** Two invariants:
1. **Append-only**: No `DELETE`, `UPDATE`, or `CLEAR` APIs exist for audit trails. Entries can only be created.
2. **Privacy hashing**: Recipient identifiers (phone numbers, email addresses) are SHA-256 hashed before writing to audit logs:

$$\text{recipient\_hash} = \text{SHA-256}(\text{raw\_recipient\_string})$$

This means audit logs prove that notifications were sent without exposing who received them.

### Q21. What is the enrollment liveness challenge?
**A.** To prevent voiceprint spoofing during enrollment, the system uses a **challenge-response protocol**:
1. Server generates a random phrase (e.g., "blue mountain running clock 847")
2. Caller must speak this exact phrase
3. The `LivenessChecker.verify()` validates that the audio matches the challenge
4. If verification fails, the session is rejected and does NOT count toward enrollment

Additionally, enrollment requires **≥3 capture sessions on distinct UTC calendar days**. This prevents an attacker from enrolling a voiceprint by recording a target in a single sitting.

---

## SECTION 5: Scalability & Performance

### Q22. What are the ingestion gateway's scalability specs?
**A.**
| Parameter | Value |
|---|---|
| Max concurrent streams | 50,000 |
| Rate limit per tenant | 100 RPS (token bucket, burst: 200) |
| Stream buffer depth | 8 chunks (bounded channel for backpressure) |
| Downstream timeout | 250ms |
| Circuit breaker | Enabled by default |
| Memory per stream | ~4KB (goroutine stack) |

When a tenant exceeds rate limits, the gateway returns gRPC `ResourceExhausted` (code 8). When downstream processing slows, the bounded Go channel applies natural TCP/gRPC backpressure to the client.

### Q23. How does the circuit breaker work?
**A.** When `EnableCircuitBreaker` is true (default), the gateway monitors downstream error rates. If errors exceed a threshold, the circuit "trips" and subsequent requests receive an immediate fail-safe response (`degraded: true`, `RECOMMEND_CALLBACK_VERIFICATION`) without actually calling the downstream service. This prevents cascading failures — if feature extraction is overloaded, the gateway stops sending it more traffic, giving it time to recover.

### Q24. How does Docker Compose manage service startup order?
**A.** The `docker-compose.yml` uses `depends_on` with `condition: service_healthy`:
- **Tier 0** (no dependencies): risk-fusion, feature-extraction, spoof-detection, enrollment
- **Tier 1** (depends on risk-fusion): policy-threshold-engine
- **Tier 2** (depends on policy): alerting-service
- **Tier 3** (depends on ALL): orchestrator

Each service has a `healthcheck` that polls its `/healthz` endpoint every 10s. The orchestrator only starts after all 6 downstream services report healthy. The ingestion gateway runs standalone (best-effort).

---

## SECTION 6: Signals & Detection Details

### Q25. What are all 4 signals that feed into risk fusion?
**A.**
| Signal | Source | What It Measures | Score Meaning |
|---|---|---|---|
| `synthesis_signal` | Spoof Detection (:8002) | Is this audio AI-synthesized? | 0.0 = natural speech, 1.0 = definitely synthetic |
| `speaker_match_signal` | Enrollment (:8003) | Does voice match enrolled voiceprint? | 0.0 = perfect match, 1.0 = completely different person |
| `content_risk_signal` | Local Ollama LLM (orchestrator) | Does the transcript contain scam language? | 0.0 = benign conversation, 1.0 = active scam |
| `contextual_signal` | Caller metadata | Is the transaction context suspicious? | 0.0 = low-risk context, 1.0 = high-risk context |

The first three are combined via **Noisy-OR** (independent evidence). The contextual signal acts as a **bounded multiplier** on the fused result.

### Q26. How does language/accent routing work in spoof detection?
**A.** The spoof detection service inspects input spectral features and routes requests to accent-cluster-specific model variants:
- `en-generic` — English (generic)
- `hi-in` — Hindi (India)
- `ta-in` — Tamil (India)
- `te-in` — Telugu (India)
- `bn-in` — Bengali (India)

If language identification fails, the system falls back to the `generic` cluster (configured via `SPOOF_DEFAULT_ACCENT_CLUSTER`). This is important for India's multilingual context — a model trained only on English would have higher false positive rates on Hindi or Tamil speakers.

### Q27. What if a signal is unavailable? How does the system handle it?
**A.** An unavailable signal has `available: false`. The system handles it as **evidence of nothing** — not evidence of safety:
- The Noisy-OR formula **skips** unavailable signals (they're excluded from the product)
- If ALL signals are unavailable, the fusion engine returns `degraded: true` with `risk_score = 0.40` (the moderate threshold) and `confidence = 0.0`
- The explanation string says "synthesis check unavailable" or "no enrolled voiceprint on file" — making the gap visible to human operators

This is the key difference from "fail open" systems that treat missing data as `score = 0.0`.

---

## SECTION 7: Policy Engine & Tenant Configuration

### Q28. How does the policy engine differ from the fusion engine?
**A.** They serve different purposes:
- **Fusion engine**: Produces a **universal** risk score using audited, deterministic math. Same math for all tenants.
- **Policy engine**: Applies **tenant-specific** thresholds to the universal score. Different tenants may have different risk tolerances.

Example: Fusion produces risk_score = 0.65 for both tenants. But:
- Bank A (conservative): callback_threshold = 0.30 → triggers `RECOMMEND_CALLBACK_VERIFICATION`
- Fintech B (aggressive): callback_threshold = 0.70 → returns `PROCEED`

### Q29. What are the configurable policy parameters?
**A.**
| Parameter | Default | Description |
|---|---|---|
| `callback_verification_threshold` | 0.40 | Score at which callback verification is recommended |
| `supervisor_escalation_threshold` | 0.70 | Score at which supervisor involvement is required |
| `block_threshold` | 0.90 | Score at which auto-block fires (if enabled) |
| `auto_block_enabled` | **false** | Must be explicitly opted into — mandatory safety gate |

### Q30. What happens when a policy is updated?
**A.** Three things:
1. `policy_version` is **incremented** (atomic counter)
2. An **immutable audit entry** is created for each changed field, recording: action, field name, old value, new value, actor identity, timestamp
3. The old configuration is gone — only the current version and the audit log survive (the audit log IS the history)

---

## SECTION 8: Frontend & Integration

### Q31. How does the frontend communicate with 8 different backend services?
**A.** Through a **Vite proxy layer** that dynamically routes requests:

```
Frontend → /api/8080/v1/pipeline/process
Vite proxy → localhost:8080/v1/pipeline/process

Frontend → /api/8000/v1/assess
Vite proxy → localhost:8000/v1/assess
```

The URL pattern `/api/{port}/path` is parsed by the proxy, which extracts the port number and forwards to the correct service. In production, this would be replaced by an API gateway (Kong, Envoy, etc.).

### Q32. How does the frontend handle audio recording for pipeline tests?
**A.** The pipeline tester page uses the Web Audio API with a specific constraint for the backend:
1. `navigator.mediaDevices.getUserMedia()` captures audio at 16kHz mono
2. `MediaRecorder` collects chunks as WebM
3. On stop: WebM is decoded via `AudioContext.decodeAudioData()`
4. Float32 samples are converted to **Int16 PCM** (the backend expects 16-bit PCM, not float)
5. PCM bytes are base64-encoded and sent to the orchestrator

**Simultaneous transcription**: The browser's `SpeechRecognition` API runs in parallel, filling the transcript field in real-time while recording.

### Q33. Is any data on the frontend hardcoded?
**A.** No. Every data point comes from a real API call:
- Service health: live `/healthz` polling every 12-15 seconds
- Alerts: live `GET /v1/tenants/{t}/alerts` polling every 5 seconds
- Pipeline results: real `POST /v1/pipeline/process` to the orchestrator
- Enrollment: real `POST /enroll`, `POST /session`, `GET /status`, `POST /revoke`, `GET /audit`
- Policy: real `GET /policy` on load, `PUT /policy` on save
- Fusion sandbox: real `POST /v1/assess` to risk-fusion-engine

---

## SECTION 9: Design Trade-offs & Justifications

### Q34. Why is the fusion engine code hand-written, not auto-generated?
**A.** The `fusion.py` file is the only component that a regulator would audit. It contains the math that decides whether a financial transaction should proceed or be blocked. Every design decision (Noisy-OR vs averaging, multiplier bounds, threshold values) is a **business/liability** decision, not just an engineering one. The file is extensively documented with inline comments explaining the "why" behind each formula. Auto-generation would obscure these decisions and make regulatory audit impractical.

### Q35. Why Noisy-OR instead of a trained ML model for fusion?
**A.** Three reasons:
1. **Determinism**: Same inputs always produce the same output. ML models can have stochastic elements (dropout, batch normalization) that produce slightly different outputs.
2. **Auditability**: A regulator can read the formula and verify it. They cannot audit a neural network's weights.
3. **Explainability**: The explanation string is built from explicit if/else logic on individual signals. A trained model would require a separate explainability layer (LIME, SHAP) that adds complexity and approximation.

### Q36. Why bounded context multiplier instead of including context in Noisy-OR?
**A.** Including context in Noisy-OR would allow a high-risk transaction context alone (with clean acoustic signals) to produce a high risk score. This would mean the system is "accusing someone of voice fraud based on metadata alone" — that's a false positive that erodes trust. The bounded multiplier ensures context can **nudge** acoustic evidence up or down by 15-35%, but can never independently drive a high-risk decision.

### Q37. Why use a local Ollama LLM instead of a cloud API for content risk?
**A.** Privacy-first architecture — zero data leaves the device:
- **Local Ollama (qwen3:4b)**: All inference runs on-device, no API keys needed, full DPDP/GDPR compliance, ~3-8s inference on CPU
- **Cloud APIs (removed)**: Would require sending call transcripts to external servers, violating the platform's core privacy commitment
- **Fallback chain**: If Ollama is unavailable, the system falls back to the built-in multilingual NLP classifier (regex/intent-based, <1ms). If all analyzers fail, the signal returns `available: false` — the platform continues with acoustic signals alone. Content risk is an additive signal, not a dependency.

The architecture supports swapping the `assess_content_risk()` implementation without changing any other service.

### Q38. Why does enrollment require 3 sessions on different days?
**A.** Two security reasons:
1. **Prevents single-recording attack**: An attacker who physically records a target during one meeting cannot complete enrollment because they'd need to return on 2 more days.
2. **Voice variability**: Human voices vary across days (hydration, sleep, ambient noise). Multiple sessions ensure the voiceprint captures natural variability, reducing false rejections during verification.

---

## SECTION 10: Rapid-Fire Technical Questions

### Q39. What is the proto contract between services?
**A.** Defined in `proto/risk_assessment.proto`:
- `RiskSignal` message: score (float64), confidence (float64), available (bool), detail (string)
- `RiskAssessmentRequest`: 3 required signals + optional content_risk_signal
- `RiskAssessmentResponse`: fused risk_score, confidence, actions[], explanation, degraded flag
- `RecommendedAction` enum: PROCEED, RECOMMEND_CALLBACK_VERIFICATION, RECOMMEND_MFA_STEP_UP, RECOMMEND_SUPERVISOR_ESCALATION, BLOCK_PENDING_VERIFICATION

### Q40. What database does the system use?
**A.** Currently **in-memory** storage for enrollment data, policy configurations, and audit logs. This is a deliberate demo-stage decision — the architecture supports plugging in any persistent store (PostgreSQL, DynamoDB, etc.) behind the existing data access interfaces. The in-memory approach means the system starts instantly with no database dependencies.

### Q41. What happens to a risk score of exactly 0.40?
**A.** It triggers `RECOMMEND_MFA_STEP_UP` (moderate risk). The thresholds use `>=`:
- `< 0.40` → PROCEED
- `>= 0.40` → RECOMMEND_MFA_STEP_UP
- `>= 0.70` → RECOMMEND_SUPERVISOR_ESCALATION + RECOMMEND_CALLBACK_VERIFICATION

### Q42. Can the system produce false positives? How are they handled?
**A.** Yes, any fraud detection system can produce false positives. Satya mitigates this through:
1. **Recommendations, not blocks**: By default, the system only recommends actions to human operators. Auto-blocking requires explicit opt-in.
2. **Explainable decisions**: Every response includes a human-readable explanation (e.g., "moderate risk (0.45): no significant synthesis artifacts; no enrolled voiceprint on file; transaction context is elevated risk"). Operators can override.
3. **Tunable thresholds**: Each tenant can adjust thresholds to their risk tolerance. A bank with many false positives can raise their callback threshold from 0.40 to 0.55.
4. **Confidence reporting**: A high risk score with low confidence signals "the system thinks there's risk but isn't very sure" — operators can weight this differently than high-risk/high-confidence.

### Q43. How is RBAC implemented in the enrollment service?
**A.** Role-based access control uses HTTP headers:
- `X-Actor-Id`: Identifies who is performing the action (audit trail)
- `X-Actor-Role`: Must be `tenant_admin` for enrollment start, revocation, and audit access
- Operations without admin role are rejected with HTTP 403

### Q44. What is the difference between risk_score and confidence?
**A.**
- **risk_score** (0.0-1.0): "How suspicious is this call?" — the threat level
- **confidence** (0.0-1.0): "How much should you trust the risk_score?" — the model's self-assessment

Example: risk_score=0.8, confidence=0.9 means "very likely suspicious, and the system is very sure." But risk_score=0.8, confidence=0.2 means "looks suspicious, but the system isn't confident — could be wrong."

### Q45. What is the deployment model?
**A.** Docker Compose for development and demo. Each service has its own `Dockerfile`. The compose file defines the full stack with health checks, dependency ordering, and a bridge network. For production:
- **Kubernetes** with HPA (horizontal pod autoscaling) per service
- **Helm charts** for parameterized deployment
- **Istio/Envoy** service mesh for mTLS, circuit breaking, and observability
- **PostgreSQL/DynamoDB** replacing in-memory stores
- **Kafka/Pub-Sub** replacing REST-based alert dispatch

### Q46. What is the total response latency target?
**A.** The system aims for **< 300ms p99 latency** for the full pipeline:
- Feature extraction: ~50ms (spectrogram + embedding)
- Parallel detection: ~100ms (spoof + enrollment in parallel)
- LLM content analysis: ~2s (async, non-blocking)
- Risk fusion: ~5ms (pure math)
- Policy evaluation: ~2ms (threshold comparison)
- Total without LLM: ~160ms. With LLM: ~2.2s (but LLM runs in parallel with other signals)

### Q47. How does the system handle a new tenant onboarding?
**A.** The policy engine creates a default configuration with safe defaults:
- `callback_verification_threshold`: 0.40
- `supervisor_escalation_threshold`: 0.70
- `block_threshold`: 0.90
- `auto_block_enabled`: **false** (mandatory default)
- `policy_version`: 1

The tenant can then enroll subjects (voiceprints), adjust thresholds, and optionally enable auto-blocking through the dashboard.

### Q48. What ML models are used?
**A.**
| Component | Model | Purpose |
|---|---|---|
| Feature Extraction | Log-Mel Spectrogram | 80-band spectral decomposition |
| Speaker Embedding | d-vector / ResNet | 192-dimensional voice identity vector |
| Spoof Detection | AASIST / ResNet variant | Classify bonafide vs synthesized speech |
| Language ID | Accent classifier | Route to region-specific spoof models |
| Content Risk | Local Ollama LLM (qwen3:4b) | Transcript scam analysis |

### Q49. What is the "shadow mode" in spoof detection?
**A.** Shadow mode allows deploying a new model version alongside the production model. Both models score every request, but only the production model's score is returned to the caller. The shadow model's scores are logged for offline comparison. When the shadow model demonstrates equal or better performance, it can be promoted to production without downtime.

### Q50. How would you scale this to 10 million calls per day?
**A.** 
1. **Ingestion**: Multiple Go gateway instances behind a load balancer (each handles 50K concurrent streams)
2. **Feature extraction**: GPU-accelerated pods with HPA scaling on CPU/memory
3. **Spoof detection**: GPU inference pods with model serving (TorchServe/Triton)
4. **Enrollment**: Sharded by tenant_id with a persistent database
5. **Fusion/Policy**: Stateless, horizontally scalable — add pods as needed
6. **Alerting**: Kafka-based event bus replacing REST dispatch, consumer groups for parallelism
7. **Estimated infrastructure**: ~20 pods (8 vCPU each) for 10M calls/day (~115 calls/second)

---

*Document prepared for SIH 2026 — Prime Vector / Satya.*
*Last updated: September 2026.*
