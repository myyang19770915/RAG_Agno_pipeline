# Final Productization Batch Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Finish the last productization pass for ingestion CLI, observability, policy wiring, docs, verification, and git sync without broad refactors.

**Architecture:** Keep the existing project shape intact. Extend the stdlib observability helpers first, then wire them into retrieval and the ingestion CLI. Productize the ingestion CLI around stable JSON summaries and env-driven preflight/runner selection while preserving the existing injected-runner test seam. Tighten policy/backend env helpers with safe defaults and fallback reasons.

**Tech Stack:** Python, pytest, argparse, json, existing rag_ingest modules, git

---

### Task 1: Observability primitives
- Add failing tests for stable structured event shape, timing metadata, and JSON-line rendering.
- Run targeted observability tests to verify RED.
- Implement minimal helpers in `src/rag_ingest/observability.py`.
- Re-run targeted tests to GREEN.

### Task 2: Retrieval debug/observability wiring
- Add failing tests for stable retrieval debug stage timings and operator-facing event summaries.
- Run `tests/rag_ingest/test_retriever_core.py` to verify RED.
- Implement minimal retrieval timing/event wiring in `src/rag_ingest/retriever_core.py`.
- Re-run targeted tests to GREEN.

### Task 3: Ingestion CLI productionization
- Add failing tests for subcommands/modes, validate-only summaries, missing dependency errors, and smoke summaries.
- Run `tests/rag_ingest/test_ingest_documents_script.py` to verify RED.
- Implement minimal CLI support in `scripts/ingest_documents.py`, preserving injected runner seams.
- Re-run targeted tests to GREEN.

### Task 4: Policy/backend wiring
- Add failing tests for richer env policy summary/fallback behavior and backend option visibility.
- Run targeted policy/backend tests to verify RED.
- Implement minimal helper changes in `src/rag_ingest/policy_config.py`, `src/rag_ingest/agno_runtime.py`, and `src/rag_ingest/agno_backend_factory.py`.
- Re-run targeted tests to GREEN.

### Task 5: Docs + verification + git
- Update `README.md`, `docs/runbooks/rag-ingestion-operations.md`, and `NEXT_STEPS.md` to match implemented behavior.
- Run targeted changed-area tests plus a stable regression slice.
- Run one practical smoke path if local dependencies allow.
- Commit and push the finished batch.
