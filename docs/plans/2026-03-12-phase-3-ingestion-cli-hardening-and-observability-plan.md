# Phase 3: Ingestion CLI Hardening and Observability Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Turn the current ingestion CLI from a minimal entrypoint into a more usable operational tool, while extending observability and debug outputs in a lightweight, production-helpful direction.

**Architecture:** Build out the ingestion CLI first because it is the most immediate usability gap: add env-driven defaults, dry-run style validation, and clearer summary outputs. Then extend observability with structured debug metadata and simple log/event shaping that can be reused by retrieval and ingest operations without forcing a heavy logging framework.

**Tech Stack:** Python, pytest, argparse, existing rag_ingest modules, stdlib timing/json/path utilities

---

### Task 1: Add env-driven defaults to ingestion CLI

**Files:**
- Modify: `scripts/ingest_documents.py`
- Test: `tests/rag_ingest/test_ingest_documents_script.py`

**Step 1: Write the failing test**

Add a test asserting `main(...)` can read default source system / chunk settings from env when args are omitted.

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src:. pytest tests/rag_ingest/test_ingest_documents_script.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Support env defaults such as:
- `RAG_SOURCE_SYSTEM`
- `RAG_CHUNK_SIZE`
- `RAG_CHUNK_OVERLAP`

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src:. pytest tests/rag_ingest/test_ingest_documents_script.py -v`
Expected: PASS

### Task 2: Add ingestion CLI validation summary

**Files:**
- Modify: `scripts/ingest_documents.py`
- Test: `tests/rag_ingest/test_ingest_documents_script.py`

**Step 1: Write the failing test**

Add a test asserting CLI returns a clear preflight-style summary containing source path, source system, and effective config fields before runner execution.

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src:. pytest tests/rag_ingest/test_ingest_documents_script.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Add a stable `config` section in the returned/printed summary.

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src:. pytest tests/rag_ingest/test_ingest_documents_script.py -v`
Expected: PASS

### Task 3: Add structured event helper

**Files:**
- Modify: `src/rag_ingest/observability.py`
- Modify: `tests/rag_ingest/test_observability.py`

**Step 1: Write the failing test**

Add a test for `build_event(name, **fields)` returning a dict with:
- `event`
- `timestamp`
- merged fields

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src:. pytest tests/rag_ingest/test_observability.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Implement a tiny helper with ISO timestamp generation.

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src:. pytest tests/rag_ingest/test_observability.py -v`
Expected: PASS

### Task 4: Add retrieval debug timing fields

**Files:**
- Modify: `src/rag_ingest/retriever_core.py`
- Modify: `tests/rag_ingest/test_retriever_core.py`

**Step 1: Write the failing test**

Add a test asserting `include_debug=True` returns timing-like fields in debug summary, e.g. `elapsed_ms` or stage timing metadata.

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src:. pytest tests/rag_ingest/test_retriever_core.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Use `timed_call(...)` or equivalent to capture whole retrieval elapsed time in debug output.

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src:. pytest tests/rag_ingest/test_retriever_core.py -v`
Expected: PASS

### Task 5: Add ingest CLI smoke-friendly doc updates

**Files:**
- Modify: `README.md`
- Modify: `docs/runbooks/rag-ingestion-operations.md`

**Step 1: Add docs for**
- ingestion CLI env defaults
- summary output fields
- expected failure modes / preflight behavior

**Step 2: Verify docs mention**

Run:
```bash
grep -n "ingest_documents\|RAG_SOURCE_SYSTEM\|RAG_CHUNK_SIZE\|preflight\|elapsed_ms" README.md docs/runbooks/rag-ingestion-operations.md
```
Expected: matches present

### Task 6: Verification and commit

**Step 1: Run targeted tests**

Run:
```bash
PYTHONPATH=src:. pytest tests/rag_ingest/test_ingest_documents_script.py \
  tests/rag_ingest/test_observability.py \
  tests/rag_ingest/test_retriever_core.py -v
```
Expected: PASS

**Step 2: Run stable regression slice**

Run:
```bash
PYTHONPATH=src:. pytest tests/rag_ingest/test_policy_config.py \
  tests/rag_ingest/test_run_agno_specialist_script.py \
  tests/rag_ingest/test_http_embedding_adapter.py \
  tests/rag_ingest/test_http_reranker.py \
  tests/rag_ingest/test_rerank.py \
  tests/rag_ingest/test_retriever_tool.py -v
```
Expected: PASS
