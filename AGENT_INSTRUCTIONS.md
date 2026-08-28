# AI Agent Instructions & System Guardrails
### Voice Integrity & Impersonation Prevention Platform

> **IMPORTANT FOR ALL AI AGENTS & ASSISTANTS:**
> Read this document completely before performing any code generation, modification, refactoring, or bug fixing in this repository. These rules ensure that even lightweight or lower-capability LLMs cannot break the core security, compliance, or safety guarantees of the platform.

---

## 🚫 1. Absolutely Protected Core Logic (DO NOT ALTER WITHOUT PERMISSION)

The following files contain hand-written, regulator-audited compliance logic and contracts. **No AI Agent is permitted to modify these files without explicit human confirmation:**

1. 🛑 `services/risk-fusion-engine/app/fusion.py`
   - Encodes bank compliance math, Noisy-OR acoustic fusion, and contextual multiplier bounds (0.85x–1.35x).
   - Covered by 8 Hypothesis property-based tests (200 runs each).
2. 🛑 `proto/risk_assessment.proto` & `proto/ingestion.proto`
   - Contract definitions shared across all services and client SDKs.
3. 🛑 `services/enrollment-service/app/enrollment.py` (Revocation & Audit functions)
   - Compliance-relevant audit trail generation.

---

## 🛡️ 2. Non-Negotiable System Invariants (Safety Constraints)

Every AI Agent MUST adhere to these 5 architectural principles. Any code change that breaks any of these invariants is a critical system defect:

### Invariant 1: Never Fail Open (DESIGN.md §3 & §4.7)
- If a downstream model, network call, or service fails or times out, the system **MUST NOT** default to "safe" (score 0.0).
- Signal responses must return `available: false` or `degraded: true` and recommend manual callback verification (`RECOMMEND_CALLBACK_VERIFICATION`).

### Invariant 2: Zero Raw Audio Retention (DESIGN.md §7)
- **Raw audio MUST NEVER be written to disk, databases, or log files.**
- Audio bytes exist transiently in memory only during feature extraction.
- **Verification:** `test_privacy.py` and `test_no_raw_audio.py` in all services must pass.

### Invariant 3: Opt-In Auto-Block Gate (DESIGN.md §4.7)
- `auto_block_enabled` **MUST default to `False`** for all tenant policy configurations.
- If `auto_block_enabled == False`, the policy engine **MUST NEVER** output `BLOCK_PENDING_VERIFICATION`, regardless of risk score (including 1.0).

### Invariant 4: Append-Only Immutable Audit Logs (DESIGN.md §4.8)
- Audit log stores have no `delete`, `update`, `clear`, or `remove` methods.
- Recipients in audit logs MUST be SHA-256 hashed. Never write raw phone numbers, emails, or names to audit logs.

### Invariant 5: Deterministic & Monotonic Risk Scoring
- Given the same input signals, `fuse()` must always return the exact same output.
- Increasing suspiciousness in acoustic signals must monotonically increase or maintain the fused risk score (never decrease it).

---

## 🧪 3. Mandatory Agent Verification Protocol

Before declaring any task, bug fix, or feature complete, the AI Agent **MUST** run the test suite for the affected component and verify that **100% of tests pass**:

```bash
# Run tests for Python services
cd services/<service-name> && python -m pytest tests/ -v

# Run tests for Go Ingestion Gateway
cd services/ingestion-gateway && go test -v ./...

# Run tests for Node SDK
cd sdk/node && npm test

# Run tests for Python SDK
cd sdk/python && python -m pytest tests/ -v
```

**Rule:** If a test fails after your edit, you MUST NOT swallow the error or modify the test assertion to pass artificially. You must fix the root cause in the service logic.

---

## 📋 4. Service Architecture & Port Mapping Reference

When generating network calls or service integrations, use these exact default ports:

| Microservice | Language / Framework | Port | Primary Endpoint |
|---|---|---|---|
| `risk-fusion-engine` | Python / FastAPI | `8000` | `POST /v1/assess` |
| `feature-extraction-service` | Python / FastAPI | `8001` | `POST /v1/extract` |
| `spoof-detection-service` | Python / FastAPI | `8002` | `POST /v1/detect` |
| `enrollment-service` | Python / FastAPI | `8003` | `POST /v1/tenants/{id}/enroll` |
| `policy-threshold-engine` | Python / FastAPI | `8004` | `POST /v1/evaluate` |
| `alerting-service` | Python / FastAPI | `8005` | `POST /v1/events` |
| `ingestion-gateway` | Go / gRPC | `50051` (gRPC), `8080` (HTTP) | `voiceintegrity.v1.IngestionGateway` |

---

## 💡 5. Prompt Pattern for Delegating Work to Other Agents

If you are delegating a sub-task to another AI agent, provide a tight specification using this exact format:

```text
TASK: Implement [service-name] in [language/framework].

CONTRACT: Must consume/produce types matching [proto/file-path].

REQUIREMENTS:
1. [Requirement 1 with reference to DESIGN.md section]
2. [Requirement 2]
3. Enforce Invariant: [Relevant Invariant from AGENT_INSTRUCTIONS.md]

DO NOT:
- Do not modify files in services/risk-fusion-engine/
- Do not persist raw audio bytes
- Do not change proto field numbers

VERIFICATION:
Run `[test command]` and ensure all tests pass cleanly before returning.
```
