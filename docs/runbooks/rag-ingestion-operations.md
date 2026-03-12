# RAG Ingestion Operations

## Scope
這份 runbook 聚焦在：
- version-aware ingestion 的基本操作觀念
- 本機 / LAN 環境下的 retrieval wiring
- smoke 驗證路徑
- timeout / fallback 的實際排障方式

## latest-active rule
所有 production retrieval 預設都應過濾：
- `is_latest=true`
- `is_active=true`

## version_fingerprint rule
- 同一個 `document_key` + 相同 `version_fingerprint` → skip
- 同一個 `document_key` + 不同 `version_fingerprint` → 建立新版本，並將舊版本標記為 superseded / inactive

## Local setup
1. 複製安全範本：
   ```bash
   cp .env.example .env
   ```
2. 至少設定：
   ```bash
   export RAG_QDRANT_URL=http://127.0.0.1:6333
   export RAG_QDRANT_COLLECTION=documents_live_hybrid_smoke
   export RAG_DENSE_MODEL=BAAI/bge-small-en-v1.5
   export RAG_SPARSE_MODEL=Qdrant/bm25
   export AGNO_MODEL=openai:gpt-5-mini
   export OPENAI_API_KEY=your_key_here
   ```
3. 預設路徑使用 FastEmbed dense + sparse，不需要另外開 embedding/reranker HTTP 服務。

## Quick smoke path
先跑穩定 CI-like 子集合，確認基本 wiring 沒壞：
```bash
PYTHONPATH=src pytest -q \
  tests/rag_ingest/test_http_embedding_adapter.py \
  tests/rag_ingest/test_http_reranker.py \
  tests/rag_ingest/test_embedding_provider.py \
  tests/rag_ingest/test_rerank.py \
  tests/rag_ingest/test_agno_backend_factory.py \
  tests/rag_ingest/test_citation_utils.py \
  tests/rag_ingest/test_pre_retrieval.py \
  tests/rag_ingest/test_retrieval_filters.py \
  tests/rag_ingest/test_retrieval_fusion.py \
  tests/rag_ingest/test_retriever_schemas.py \
  tests/rag_ingest/test_retriever_core.py \
  tests/rag_ingest/test_retriever_tool.py
```

如果要驗證 live specialist path：
```bash
PYTHONPATH=src:. python3 scripts/run_agno_specialist.py "what is this document about?"
```

如果要先驗證 ingestion CLI contract：
```bash
PYTHONPATH=src:. python3 scripts/ingest_documents.py validate --source-path /data/docs
PYTHONPATH=src:. python3 scripts/ingest_documents.py ingest --source-path /data/docs --db-path /tmp/rag-ingest.db
PYTHONPATH=src:. python3 scripts/ingest_documents.py smoke --source-path /data/docs
```

CLI 也支援從 env 載入預設值，方便 smoke / cron / batch job：
```bash
export RAG_SOURCE_SYSTEM=local-folder
export RAG_CHUNK_SIZE=500
export RAG_CHUNK_OVERLAP=50
export RAG_SQLITE_DB_PATH=/tmp/rag-ingest.db
export RAG_INGEST_RUNNER=local_folder
PYTHONPATH=src:. python3 scripts/ingest_documents.py ingest --source-path /data/docs
```

有效設定規則：
- `--source-system` 未提供時，讀 `RAG_SOURCE_SYSTEM`
- `--chunk-size` 未提供時，讀 `RAG_CHUNK_SIZE`，否則回退 `500`
- `--chunk-overlap` 未提供時，讀 `RAG_CHUNK_OVERLAP`，否則回退 `50`
- `--db-path` 未提供時，讀 `RAG_SQLITE_DB_PATH`
- 未指定 subcommand 時，預設等同 `ingest`

CLI 三種模式：
- `validate`：只做 preflight，回傳 `supported_files` / `source_exists` / `runner`
- `ingest`：可用注入 runner，或使用內建 `local_folder` runner（SQLite + FakeQdrant summary）
- `smoke`：回傳固定 JSON smoke summary，適合 CI / shell pipeline / operator 檢查

穩定輸出 shape 至少包含：
- `command`
- `status`
- `config.*`
- `preflight.*`
- `timing.elapsed_ms`
- `event`

`ingest` 模式常見 summary 欄位：
- `summary.documents_indexed`
- `summary.qdrant_points`
- `summary.embedding_provider`
- `summary.db_path`

`preflight` 區塊的用途是先確認 effective config、來源是否存在、可掃描檔案數、與目前 runner，再進入真正 ingest。這讓 CLI 更適合 shell pipeline、job runner、或 smoke 測試比對。

若缺少 runtime 依賴，CLI 會 fail-fast 並給清楚訊息，例如：
- `Missing runtime dependency for ingest_documents CLI: qdrant_client`
- `Local folder ingest requires --db-path or RAG_SQLITE_DB_PATH.`

## Retrieval debug / observability
當你要排查 retrieval 品質或延遲時，可在 retrieval request / tool path 開 `include_debug=True`。

目前 debug summary 的重點是穩定 shape，而不是完整 tracing，至少會帶：
- `retrieval_summary.vector_candidates`
- `retrieval_summary.keyword_candidates`
- `retrieval_summary.fused_candidates`
- `retrieval_summary.reranked_candidates`
- `retrieval_summary.elapsed_ms`
- `timings.prepare_queries.elapsed_ms`
- `timings.vector_search.elapsed_ms`
- `timings.keyword_search.elapsed_ms`
- `timings.fusion_filter_rerank.elapsed_ms`
- `timings.total.elapsed_ms`
- `event`（例如 `retrieval.completed`）

建議：
- smoke 驗證先關閉，保持輸出精簡
- 排障或調參時再打開 `include_debug`
- 若在 smoke 中看到 `timings.vector_search.elapsed_ms` 或 `timings.keyword_search.elapsed_ms` 明顯飆升，先檢查外部 retrieval backend
- 若 `timings.fusion_filter_rerank.elapsed_ms` 飆升，優先檢查 rerank / filter policy 與外部 reranker

## Policy defaults from env
specialist / retrieval wiring 目前支援從 env 載入保守 policy：
```bash
export RAG_REWRITE_MODE=none
export RAG_HISTORY_MODE=false
export RAG_RERANKER_PROVIDER=none
export RAG_EMBEDDING_PROVIDER=fastembed
export RAG_RETRIEVAL_FALLBACK_MODE=lightweight
```

safe defaults：
- `rewrite_mode=none`
- `history_mode=false`
- `rerank_provider=none`
- `embedding_provider=fastembed`
- `fallback_mode=lightweight`

若值不合法，會自動回退到 safe defaults，而不是把未知 policy 直接帶進 live path。`load_policy_from_env()` 也會保留 requested value 與 fallback reason（`default` / `env` / `invalid`），方便 operator 快速看出目前是否真的吃到預期 policy。

## LAN embedding path
若 dense embedding 由 LAN 上的 OpenAI-compatible 服務提供：
```bash
export RAG_EMBEDDING_PROVIDER=openai_compatible
export RAG_EMBEDDING_BASE_URL=http://192.168.1.10:8000
export RAG_EMBEDDING_MODEL=Qwen/Qwen3-Embedding-0.6B
export RAG_EMBEDDING_TIMEOUT_SECONDS=10
```

預期 API：
- endpoint: `POST /v1/embeddings`
- payload: `{ "model": "...", "input": ["..."] }`

## LAN reranker path
若要使用 Qwen reranker HTTP 服務：
```bash
export RAG_RERANKER_PROVIDER=http_qwen
export RAG_RERANKER_BASE_URL=http://192.168.1.10:8090
export RAG_RERANKER_MODEL=Qwen/Qwen3-Reranker-0.6B
export RAG_RERANKER_TIMEOUT_SECONDS=10
```

預期 API：
- endpoint: `POST /score`
- payload: `{ "model": "...", "queries": ["..."], "items": ["..."] }`

## Timeout and fallback behavior
### Embedding
- `HttpEmbeddingAdapter` 會對 HTTP request 帶 `timeout`
- 若服務逾時、無法連線、或回傳 4xx/5xx，會拋出清楚的 `RuntimeError`
- 這是 request-level 明確失敗，不會默默吞掉

### Reranker
- `HttpQwenReranker` 會對 HTTP request 帶 `timeout`
- 若 request 逾時或失敗，會拋出清楚的 `RuntimeError`
- 若 `RAG_RERANKER_PROVIDER=none`，系統維持既有 lightweight rerank
- 若設定 `http_qwen`，但 reranker 在建構階段失敗，backend wiring 會回退到 lightweight rerank，避免整體 backend 初始化直接炸掉

## Dense + sparse ingestion notes
每個 chunk 可攜帶：
- dense vector
- sparse vector
- version-aware payload metadata

Qdrant hybrid retrieval 建議在 ingestion 時就同時寫入 dense + sparse 表示，讓 retrieval 可直接重用同一批 version-governed chunk records。

## Qdrant collection expectations
Qdrant collection 應配置：
- named dense vectors
- named sparse vectors
- 對 document/version/status 欄位建立 payload indexes

## Basic troubleshooting
### 1. Backend 初始化就失敗
先檢查必要 env：
- `RAG_QDRANT_URL`
- `RAG_QDRANT_COLLECTION`
- `RAG_SPARSE_MODEL`
- 若走 FastEmbed：`RAG_DENSE_MODEL`
- 若走 HTTP embeddings：`RAG_EMBEDDING_BASE_URL`、`RAG_EMBEDDING_MODEL`

### 2. HTTP embedding request failed
- 確認 `RAG_EMBEDDING_BASE_URL` 指向服務根，不是錯誤 path
- 確認服務真的有 `/v1/embeddings`
- 拉長 `RAG_EMBEDDING_TIMEOUT_SECONDS`
- 若只是要先驗證整體 retrieval，先切回：
  ```bash
  export RAG_EMBEDDING_PROVIDER=fastembed
  ```

### 3. HTTP reranker request failed
- 確認服務真的有 `/score`
- 確認 `RAG_RERANKER_MODEL` 是服務接受的名字
- 拉長 `RAG_RERANKER_TIMEOUT_SECONDS`
- 若要先恢復既有行為：
  ```bash
  export RAG_RERANKER_PROVIDER=none
  ```

### 4. 想排除 LAN 依賴
先用預設保守路徑：
```bash
export RAG_EMBEDDING_PROVIDER=fastembed
export RAG_RERANKER_PROVIDER=none
```

## Repository hygiene
- `.env.example` 只放安全範例，不放 secrets
- `.github/workflows/tests.yml` 只跑不依賴私有 infra 的穩定子集合
- `LICENSE` 為 MIT

## Nightly cleanup
建議在離峰時段執行：
- 刪除 retention 之外、已 superseded 且 inactive 的 Qdrant points

## Reconciliation
定期比對：
- DB active chunk counts
- Qdrant active point counts
