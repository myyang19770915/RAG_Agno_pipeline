# Phase 2: Ingestion CLI, Observability, and Policy Wiring Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a usable ingestion CLI, lightweight observability/debug surfaces, and more explicit config/policy wiring on top of the current runnable RAG + Agno project.

**Architecture:** Start with the most user-facing gap: a stable CLI entrypoint for ingestion and smoke tasks. Then add low-risk observability hooks (structured summary/debug outputs and timing visibility) before tightening env/config-driven policy selection for rewrite/rerank/provider behavior. Keep all defaults backward compatible and avoid invasive refactors.

**Tech Stack:** Python, pytest, existing rag_ingest modules, argparse/stdlib, current Qdrant/FastEmbed/HTTP adapter integrations

---

### Task 1: Add ingestion CLI entrypoint

**Files:**
- Create: `scripts/ingest_documents.py`
- Test: `tests/rag_ingest/test_ingest_documents_script.py`

**Step 1: Write the failing test**

```python
from scripts import ingest_documents


def test_ingest_documents_module_exposes_main():
    assert callable(ingest_documents.main)
```

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src:. pytest tests/rag_ingest/test_ingest_documents_script.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Create a script with:
- `main(argv=None)`
- argparse parsing for source path and source system
- a clear RuntimeError stub if full ingest wiring inputs are not supplied yet

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src:. pytest tests/rag_ingest/test_ingest_documents_script.py -v`
Expected: PASS

### Task 2: Add CLI summary output contract

**Files:**
- Modify: `scripts/ingest_documents.py`
- Test: `tests/rag_ingest/test_ingest_documents_script.py`

**Step 1: Write the failing test**

Add a test that monkeypatches the ingest runner and asserts:
- `main(...)` returns a summary dict
- script prints JSON summary

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src:. pytest tests/rag_ingest/test_ingest_documents_script.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Implement a narrow injectable runner hook so the CLI can:
- run fake ingestion in tests
- print JSON summary
- return summary dict

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src:. pytest tests/rag_ingest/test_ingest_documents_script.py -v`
Expected: PASS

### Task 3: Add lightweight observability helpers

**Files:**
- Create: `src/rag_ingest/observability.py`
- Test: `tests/rag_ingest/test_observability.py`

**Step 1: Write the failing test**

Add tests for helpers like:
- `timed_call(label, fn)` returning `(result, metadata)`
- metadata containing `label` and `elapsed_ms`

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src:. pytest tests/rag_ingest/test_observability.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Implement simple stdlib timing helpers.

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src:. pytest tests/rag_ingest/test_observability.py -v`
Expected: PASS

### Task 4: Add debug summary shaping for retrieval path

**Files:**
- Modify: `src/rag_ingest/retriever_core.py`
- Test: `tests/rag_ingest/test_retriever_core.py`

**Step 1: Write the failing test**

Add a test asserting `include_debug=True` returns a stable debug summary with counts such as:
- vector candidates count
- keyword candidates count
- fused candidates count
- reranked candidates count

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src:. pytest tests/rag_ingest/test_retriever_core.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Add a compact debug summary object without changing primary result shape.

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src:. pytest tests/rag_ingest/test_retriever_core.py -v`
Expected: PASS

### Task 5: Add env-driven policy helpers

**Files:**
- Create: `src/rag_ingest/policy_config.py`
- Test: `tests/rag_ingest/test_policy_config.py`

**Step 1: Write the failing test**

Add tests for a helper like:
- `load_policy_from_env()`

Expected fields:
- `rewrite_mode`
- `history_mode`
- `rerank_provider`
- `embedding_provider`

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src:. pytest tests/rag_ingest/test_policy_config.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Implement env parsing with safe defaults matching current behavior.

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src:. pytest tests/rag_ingest/test_policy_config.py -v`
Expected: PASS

### Task 6: Wire policy defaults into Agno specialist script

**Files:**
- Modify: `scripts/run_agno_specialist.py`
- Test: `tests/rag_ingest/test_run_agno_specialist_script.py`

**Step 1: Write the failing test**

Add a test asserting the script reads policy defaults from env helper and passes them into the live path or agent construction where appropriate.

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src:. pytest tests/rag_ingest/test_run_agno_specialist_script.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Use `load_policy_from_env()` to shape defaults while keeping explicit env/provider behavior backward compatible.

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src:. pytest tests/rag_ingest/test_run_agno_specialist_script.py -v`
Expected: PASS

### Task 7: Docs update

**Files:**
- Modify: `README.md`
- Modify: `docs/runbooks/rag-ingestion-operations.md`
- Modify: `NEXT_STEPS.md`

**Step 1: Add docs for**
- ingestion CLI usage
- observability/debug outputs
- policy env variables

**Step 2: Verify docs mention**

Run:
```bash
grep -n "ingest_documents\|include_debug\|policy\|rewrite_mode\|RAG_EMBEDDING_PROVIDER" README.md docs/runbooks/rag-ingestion-operations.md NEXT_STEPS.md
```
Expected: matches present

### Task 8: Verification

**Step 1: Run new/updated tests**

Run:
```bash
PYTHONPATH=src:. pytest tests/rag_ingest/test_ingest_documents_script.py \
  tests/rag_ingest/test_observability.py \
  tests/rag_ingest/test_policy_config.py \
  tests/rag_ingest/test_retriever_core.py \
  tests/rag_ingest/test_run_agno_specialist_script.py -v
```
Expected: PASS

**Step 2: Run stable regression subset**

Run:
```bash
PYTHONPATH=src:. pytest tests/rag_ingest/test_http_embedding_adapter.py \
  tests/rag_ingest/test_http_reranker.py \
  tests/rag_ingest/test_embedding_provider.py \
  tests/rag_ingest/test_rerank.py \
  tests/rag_ingest/test_agno_backend_factory.py \
  tests/rag_ingest/test_retriever_tool.py \
  tests/rag_ingest/test_retriever_schemas.py \
  tests/rag_ingest/test_retrieval_filters.py \
  tests/rag_ingest/test_retrieval_fusion.py -v
```
Expected: PASS
