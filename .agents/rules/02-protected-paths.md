---
trigger: always_on
---

# PROTECTED PATHS AND REVIEW MANDATES FOR AI AGENTS

1. **`services/risk-fusion-engine/app/fusion.py`**
   - This file contains hand-written, regulator-audited compliance math.
   - AI Agents MUST NOT edit or regenerate this file without explicit human approval.

2. **`proto/risk_assessment.proto`**
   - This is the contract for all microservices.
   - AI Agents MUST NOT modify field numbers, enum values, or breaking changes without explicit human approval.

3. **Revocation & Audit Trail Code Paths**
   - Any modifications to `revoke_voiceprint` in enrollment-service or `update_policy` in policy-threshold-engine are compliance-relevant.
   - Agents MUST flag changes to these files for manual human review before completing the task.
