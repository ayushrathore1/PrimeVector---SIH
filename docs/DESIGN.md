# RFC: Real-Time Voice Integrity & Impersonation Prevention Platform
Status: Draft v2 (post-review) · Owner: [you] · Reviewers: security, privacy, ML platform, compliance

## 1. Problem, restated precisely
Detect and *act on* AI-cloned/synthetic-voice impersonation during live calls,
before a high-risk action (fund transfer, credential disclosure, privileged
approval) is taken — for banks, enterprises, and telecom operators, across
Indian languages/accents, at national scale.

## 2. Non-goals (explicit, so scope doesn't creep during implementation)
- Not a general deepfake-research platform. We integrate proven techniques;
  we do not aim to publish new spoof-detection SOTA.
- Not the transaction system itself. We are a risk signal + workflow trigger
  that banking/enterprise systems call into and act on.
- Not full call recording/storage. Raw audio is transient by design (§7).
- Not fully-automated blocking in the general case (§6, liability).

## 3. Scale & SLO targets
| Metric | Target | Why |
|---|---|---|
| Peak concurrent streams (national) | 10M+ | business-hours telecom+banking load |
| Per-chunk inference p99 latency | <300ms | must arrive before the human decision |
| Availability | 99.99% | sits in financial-transaction critical path |
| Fail behavior on dependency outage | fail SAFE → "risk unknown, recommend manual verification" | never silently pass calls through |

## 4. Gaps closed in this revision (see review notes)

### 4.1 Cold start & enrollment
- No enrolled voiceprint → speaker-verification layer is SKIPPED, not faked.
  Risk score is computed from synthesis-detection + context layers only, and
  the response includes `enrollment_status: NOT_ENROLLED` so downstream
  policy can treat "no baseline to compare against" as its own risk category
  (e.g., a bank may choose to require secondary verification for ANY
  high-value call from an unenrolled voice, independent of the AI score).
- Enrollment is opt-in and initiated by the *institution* (bank/enterprise)
  enrolling its own privileged staff (CFOs, approvers), not end consumers —
  this bounds the initial rollout to a tractable, high-value population
  instead of "enroll a billion people," which is both infeasible and not
  what the PS's fraud scenario (CXO/official impersonation) actually needs.

### 4.2 Enrollment integrity (root of trust)
- Enrollment requires: (a) multi-session capture (≥3 sessions, different
  days) to avoid a single spoofed sample poisoning the voiceprint, (b) a
  liveness/anti-replay check at enrollment time (challenge phrase, not a
  static passphrase, to resist replay of a recorded/cloned enrollment
  attempt), (c) enrollment channel separate from the channel being protected
  (e.g., enroll via a verified in-app biometric flow, not over an inbound
  phone call — an inbound call is exactly the channel we don't trust).
- Voiceprints are versioned; a compromised voiceprint can be revoked and
  re-enrolled without touching the rest of the system.

### 4.3 MLOps / model lifecycle (the arms race)
- Every model (spoof detector, speaker-embedding model) is served via a
  versioned Model Registry entry, never hardcoded into a service.
- Shadow-mode evaluation: new model versions score real traffic silently
  for 2+ weeks, compared against confirmed-fraud outcomes (from bank
  chargeback/fraud-report feedback, ingested via a separate labeled-outcome
  pipeline) before being promoted to affect live decisions.
- A standing red-team function continuously generates new synthetic-voice
  samples using the latest public/commercial TTS/cloning tools and feeds
  them into the shadow-mode evaluation — detection quality is tracked as a
  monitored metric that decays over time by default, not a one-time
  benchmark.

### 4.4 Multilingual / accent architecture
- Language/accent identification runs as a cheap first-pass classifier;
  routes to accent-cluster-specific model variants where available, falls
  back to a language-agnostic acoustic model otherwise.
- Fairness requirement, enforced in CI for every model promotion: false
  positive rate and false negative rate must be measured and reported
  *per language/accent cluster*, not just in aggregate. A model with a
  materially higher FPR for any cluster fails promotion review by default.

### 4.5 Edge/on-device deployment
- The Feature Extraction + Spoof Detection services are packaged to run
  in three deployment modes against the same interface: (a) central cloud
  (default for enterprises/banks), (b) telecom-operator on-prem (audio never
  leaves the operator's network), (c) on-device SDK for high-security
  enterprise clients. Only the Risk Fusion + Policy layers require any
  data to leave the local boundary, and even then only feature vectors,
  never audio.

### 4.6 Cost / capacity design
- Cascading inference: a lightweight heuristic/energy-based pre-filter
  screens out silence/non-speech/obviously-clean segments before the full
  spoof-detection model runs, to avoid paying full inference cost on every
  audio chunk of every call. Full model only invoked on segments the
  pre-filter flags as worth scoring, or periodically as a baseline sample.

### 4.7 Liability-driven design rule (hard constraint, not a preference)
- The system NEVER unilaterally blocks a transaction. It surfaces a risk
  score + recommended action to a human decision point (the bank's own
  approval workflow, the call-center agent, the transaction-approval UI).
  Full auto-block is available only as an opt-in configuration a tenant
  explicitly enables for specific high-value thresholds, with an audit
  trail, because the liability for a wrongly-blocked transaction sits with
  whoever configured that policy, not with us by default.

### 4.8 Observability & incident response
- SLO dashboards per service (latency, error rate, FPR/FNR drift) with
  paging thresholds tied to SLO burn rate, not raw metric thresholds.
- Every model promotion and every threshold-policy change is logged to an
  immutable audit trail with actor identity — required for bank compliance
  review, and for us to be able to answer "why did this call get flagged"
  months later.
- Documented rollback runbook: any model version or policy change can be
  reverted in <5 minutes via the Model Registry / Policy Engine version
  pointer, without a code deploy.

### 4.9 Disaster recovery
- Active-active across ≥3 regions for the stateless inference services.
- Voiceprint store: regionally replicated with encryption keys held
  per-region (not a single global key), RPO <5min, RTO <15min.
- Regional failure degrades to fail-safe behavior (§3) for affected traffic
  while failover completes, never a hard outage of the calling application.

## 5. Architecture (unchanged core, gaps above layered in)
See `../proto/risk_assessment.proto` for the contract. Nine services,
detailed in the original architecture note; the two implemented in this
repo as reference implementations are `risk-fusion-engine` (the sensitive,
audit-relevant logic — implemented by hand, not delegated) and
`enrollment-service` (implements §4.1/§4.2).

## 6. What gets implemented by a senior engineer directly vs. delegated
- **By hand, reviewed personally, no exceptions:** risk fusion logic,
  enrollment integrity checks, the fail-safe/fail-open decision points,
  anything touching the voiceprint store's encryption boundary.
- **Delegated to AI coding tools, lightly reviewed:** service boilerplate,
  SDK generation, test scaffolding, CI/CD config, observability
  instrumentation wiring.

## 7. Privacy & compliance
- Raw audio: held in memory only for the duration of feature extraction,
  never written to disk or persisted centrally. Enforced by a unit test
  (see `risk-fusion-engine` for the pattern; feature-extraction service
  applies the same rule).
- Audit log stores feature-derived risk assessments and policy decisions
  only — never audio, never full transcripts.
- Data residency: voiceprint stores and audit logs for Indian financial
  institutions remain in-region, per RBI data-localization expectations;
  architecture supports per-tenant region pinning at the storage layer.

## 8. Rollout plan
1. Single pilot bank, single region, shadow mode only (score, don't act).
2. Compare shadow scores against the bank's existing fraud outcomes for
   2-4 weeks; tune thresholds against real data, not assumptions.
3. Enable live recommend-only actions (no auto-block) for the pilot.
4. Expand regions/tenants gradually; auto-block remains opt-in per tenant.
