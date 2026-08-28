---
trigger: always_on
---

# MANDATORY TEST VERIFICATION FOR AI AGENTS

AI Agents MUST NOT claim a task is completed, a bug is fixed, or a feature is built until they have executed the relevant test suites and verified that ALL tests pass cleanly:

1. **Python Microservices:** Must run `python -m pytest tests/ -v` in the relevant service directory.
2. **Go Ingestion Gateway:** Must run `go test -v ./...` in `services/ingestion-gateway`.
3. **Node SDK:** Must run `npm test` in `sdk/node`.
4. **Python SDK:** Must run `python -m pytest tests/ -v` in `sdk/python`.

If any test fails after an edit, the AI Agent MUST revert the breaking change or debug and fix the underlying issue. Never comment out failing assertions or swallow errors.
