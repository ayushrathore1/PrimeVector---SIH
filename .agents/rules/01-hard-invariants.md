---
trigger: always_on
---

# HARD INVARIANTS (NON-NEGOTIABLE SAFETY RULES FOR ALL AI AGENTS)

Any AI agent modifying code in this repository MUST comply with these rules. No agent has permission to bypass or alter these rules under any circumstances:

1. **NEVER FAIL OPEN (DESIGN.md §3 & §4.7)**
   - Missing signals, timeouts, or dependency outages MUST result in `available: false` or `degraded: true` with a cautious recommendation (`RECOMMEND_CALLBACK_VERIFICATION`).
   - Missing data must NEVER be treated as `score = 0.0` ("safe").

2. **AUDIO NON-RETENTION (DESIGN.md §7)**
   - Raw audio MUST NOT be persisted to disk, databases, or log files.
   - Do NOT add `audio_bytes` or `raw_audio` fields to stored models or domain objects.
   - Feature extraction processes audio in-memory and discards it immediately.

3. **OPT-IN AUTO-BLOCK GATE (DESIGN.md §4.7)**
   - `auto_block_enabled` MUST default to `False` for every tenant.
   - If `auto_block_enabled = False`, the system MUST NEVER output `BLOCK_PENDING_VERIFICATION`, regardless of risk score (even at 1.0).

4. **APPEND-ONLY AUDIT LOGS (DESIGN.md §4.8)**
   - Audit logs are append-only. Do NOT implement `delete`, `update`, or `clear` APIs for audit trails.
   - Recipients in audit logs MUST be SHA-256 hashed. Never store raw contact information.

5. **DETERMINISTIC FUSION SCORING**
   - Fusion logic must produce the exact same output for the exact same input signals. No randomness or wall-clock dependence in score calculation.
