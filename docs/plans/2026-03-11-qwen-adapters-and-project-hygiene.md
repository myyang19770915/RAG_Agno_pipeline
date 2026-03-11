# Qwen Adapters and Project Hygiene Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add MIT licensing, a safe environment template, CI test workflow, optional HTTP-based Qwen embedding/reranker adapters, and docs for the new optional integration path.

**Architecture:** Keep the existing FastEmbed/Qdrant retrieval path as the default. Add small injectable stdlib HTTP adapters plus minimal environment-driven wiring helpers so local OpenAI-compatible embedding and Qwen-style reranking can be enabled without destabilizing the current backend.

**Tech Stack:** Python 3.11, pytest, urllib/json stdlib HTTP, GitHub Actions.

---

### Task 1: Add failing adapter and wiring tests
- Create tests for HTTP embedding adapter request/response handling.
- Create tests for HTTP reranker request/response handling.
- Extend embedding provider/backend factory tests for env-driven optional selection.
- Run targeted pytest commands and confirm failures for missing behavior.

### Task 2: Implement minimal adapter code and wiring
- Add `src/rag_ingest/http_embedding_adapter.py`.
- Add `src/rag_ingest/http_reranker.py`.
- Extend `src/rag_ingest/embedding_provider.py` for optional openai-compatible env names.
- Extend `src/rag_ingest/agno_backend_factory.py` with a minimal helper exposing embedding provider/reranker env selections without changing default behavior.
- Run targeted tests until green.

### Task 3: Add repository hygiene files
- Add `LICENSE` with MIT text.
- Add `.env.example` with safe defaults/comments and optional local service configuration.
- Add `.github/workflows/tests.yml` for Python 3.11 pytest runs.

### Task 4: Update docs and verify
- Update `README.md` for license, env template, CI, and optional local Qwen integration.
- Update architecture docs for default vs optional embedding/reranker path.
- Run targeted tests plus impacted backend/rerank tests.
- Review `git status` and commit locally with a clear message.
