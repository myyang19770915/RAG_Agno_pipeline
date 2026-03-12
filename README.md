# RAG_Agno_pipeline

> Version-aware RAG ingestion + hybrid retrieval + Agno specialist agent runtime.

這個專案是一套 **version-aware RAG ingestion + agent-ready hybrid retriever + Agno specialist runtime** 骨架，目標是建立：

- 文件版本可治理
- 預設只查最新有效版本
- dense + sparse hybrid retrieval
- citation 可追蹤
- 可被 agent 直接調用的穩定 contract
- 可落地到 Qdrant + FastEmbed 的 live path
- 可選接本地 Qwen embedding / reranker HTTP 服務

---

## 1. 核心功能

### 文件版本治理
- 同一份文件重跑 ingest 時不重複建立 embeddings
- 文件更新時建立新版本，舊版本標記為 superseded / inactive
- 預設 retrieval 只查 `is_latest=true` 且 `is_active=true`

### Hybrid Retrieval
- dense vector retrieval
- sparse / keyword retrieval
- fusion
- rerank
- citation formatting

### Agent-ready Contract
對外以 structured schema 提供：
- `RetrieveRequest`
- `RetrieveResult`
- `RetrieveResponse`
- `retrieve_tool(request_dict, backend)`

### Runtime / Live Path
- FastEmbed runtime factory
- runtime query encoder / document encoder
- Qdrant live collection + upsert + query
- live smoke runner

---

## 2. 專案結構

```text
src/rag_ingest/
├── contracts.py                  # document_key / version_fingerprint 規則
├── db/                           # Document / DocumentVersion / session
├── services/
│   ├── versioning.py             # skip / new version / new doc 決策
│   ├── ingest_pipeline.py        # 版本感知 ingest + Qdrant upsert
│   └── job_control.py            # ingestion job / rerun / logs
├── pre_retrieval.py              # rewrite / multi-query
├── retrieval_fusion.py           # fusion (RRF)
├── retrieval_filters.py          # latest-active / history mode
├── rerank.py                     # rerank abstraction
├── citation_utils.py             # citation helper
├── retriever_schemas.py          # request / response schema
├── retriever_core.py             # retrieval pipeline core
├── retriever_tool.py             # tool-style entrypoint
├── query_encoders.py             # query encoder abstraction
├── document_encoders.py          # document encoder abstraction
├── fastembed_adapters.py         # FastEmbed runtime factory / config
├── hybrid_ingest_orchestrator.py # dense+sparse ingest preparation
├── qdrant_integration.py         # collection contract
├── qdrant_payloads.py            # payload / point id helper
├── qdrant_hybrid_live_ops.py     # hybrid live point struct
├── qdrant_retriever_backend.py   # Qdrant → retriever adapter
├── live_smoke.py                 # retrieval smoke helper
├── agno_backend_factory.py       # env/config-driven Agno backend wiring
├── agno_live_smoke.py            # minimal backend -> agent -> response smoke path
└── live_hybrid_runner.py         # runnable live hybrid validation path
```

---

## 3. 架構概念

系統可分成 6 層：

1. **Source / File Ingestion Layer**
   - 讀取來源文件
   - chunking
   - metadata 建立

2. **Version Governance Layer**
   - 決定 skip / new version / new document
   - 管理 current version / superseded version

3. **Encoding Layer**
   - query/document encoder abstraction
   - dense + sparse encoding
   - FastEmbed runtime boundary

4. **Storage Layer**
   - Qdrant dense+sparse collection
   - payload index
   - point id strategy

5. **Retrieval Layer**
   - pre-retrieval
   - dense + sparse search
   - fusion
   - latest-active filter
   - rerank
   - citation

6. **Tool / Agent Integration Layer**
   - stable request/response contract
   - `retrieve_tool(...)`

詳細說明請看：
- `docs/architecture/system-architecture.md`
- `docs/architecture/system-flow.md`

---

## 快速開始

### 需求
- Python 3.11+
- Qdrant（本機或 LAN）
- `pytest`
- `qdrant-client`
- `fastembed`（走預設 FastEmbed 路徑時需要）
- `agno` + 可用的 LLM provider（跑 Agno specialist smoke 時需要）

### 1. 本機 setup
先複製安全範本：
```bash
cp .env.example .env
```

最小本機 FastEmbed 路徑：
```bash
export RAG_QDRANT_URL=http://127.0.0.1:6333
export RAG_QDRANT_COLLECTION=documents_live_hybrid_smoke
export RAG_DENSE_MODEL=BAAI/bge-small-en-v1.5
export RAG_SPARSE_MODEL=Qdrant/bm25
export AGNO_MODEL=openai:gpt-5-mini
export OPENAI_API_KEY=your_key_here
```

### 2. Quick smoke（不依賴 LAN embedding / reranker）
先跑穩定測試子集合：
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

接著可跑 Agno specialist smoke：
```bash
PYTHONPATH=src:. python3 scripts/run_agno_specialist.py "what is this document about?"
```

### 2.1 Ingestion CLI contract
目前 repo 也提供 `scripts/ingest_documents.py` 作為 ingestion CLI 入口骨架：
```bash
PYTHONPATH=src:. python3 scripts/ingest_documents.py \
  --source-path /data/docs \
  --source-system local-folder
```

目前預設仍是安全 stub；若尚未注入實際 runner，CLI 會明確回報 wiring 尚未完成。完成 wiring 後，CLI 應輸出 JSON summary，方便後續接 shell script 或 job runner。

### 2.2 Retrieval debug / observability
若 retrieval 路徑需要額外診斷，可在 request/tool 層開 `include_debug=True`，回傳穩定 debug summary，例如：
- vector candidates count
- keyword candidates count
- fused candidates count
- reranked candidates count

這個欄位是 optional，不會改變主要 answer/result contract，但很適合 smoke、排障與延遲分析。

### 3. LAN embedding / reranker 路徑
如果 dense embedding 改由 OpenAI-compatible HTTP 服務提供：
```bash
export RAG_EMBEDDING_PROVIDER=openai_compatible
export RAG_EMBEDDING_BASE_URL=http://192.168.1.10:8000
export RAG_EMBEDDING_MODEL=Qwen/Qwen3-Embedding-0.6B
export RAG_EMBEDDING_TIMEOUT_SECONDS=10
```

如果要接 Qwen reranker HTTP 服務：
```bash
export RAG_RERANKER_PROVIDER=http_qwen
export RAG_RERANKER_BASE_URL=http://192.168.1.10:8090
export RAG_RERANKER_MODEL=Qwen/Qwen3-Reranker-0.6B
export RAG_RERANKER_TIMEOUT_SECONDS=10
```

### 3.1 Policy env vars
目前 retrieval / specialist 的保守 policy defaults 可由 env 載入：
```bash
export RAG_REWRITE_MODE=none
export RAG_HISTORY_MODE=false
export RAG_RERANKER_PROVIDER=none
export RAG_EMBEDDING_PROVIDER=fastembed
```

安全預設為：
- `rewrite_mode=none`
- `history_mode=false`
- `rerank_provider=none`
- `embedding_provider=fastembed`

`scripts/run_agno_specialist.py` 會讀取這些 policy defaults，並把它們傳進 agent tool wiring；若 env 未設定或值不合法，會自動退回上述安全預設，保持 backward compatibility。

目前 fallback / timeout 行為：
- HTTP embedding 與 HTTP reranker 都會帶明確 timeout
- HTTP request 失敗時會丟出清楚的 `RuntimeError`
- `RAG_RERANKER_PROVIDER=none` 時，維持既有 lightweight rerank fallback
- 若 `http_qwen` reranker 在建構階段失敗，backend wiring 會退回 lightweight rerank，而不是讓整個 backend 初始化失敗

### 4. 基本 troubleshooting
- 缺少必要 RAG env：`create_backend_from_env(...)` 會明確列出缺的變數
- HTTP embedding timeout / 連線錯誤：確認 `RAG_EMBEDDING_BASE_URL`、模型名、服務是否真的提供 `/v1/embeddings`
- HTTP reranker timeout / 連線錯誤：確認 `RAG_RERANKER_BASE_URL`、模型名、服務是否真的提供 `/score`
- 想先排除外部服務因素：把 `RAG_EMBEDDING_PROVIDER=fastembed`、`RAG_RERANKER_PROVIDER=none`
- FastEmbed cache/threads 調校：使用 `RAG_FASTEMBED_CACHE_DIR`、`RAG_FASTEMBED_THREADS`

### 安全提醒
- **不要把 `.env`、API keys、token.json、憑證檔提交到 Git**
- 請使用 `.env.example` 當成可提交的安全模板，真正 secrets 只放本機 `.env` 或 CI secret store
- 本 repo 已加入 `.gitignore` 來避免常見機密與快取檔案被提交

---

## 4. Mermaid Flowchart 文件

請直接查看：
- `docs/architecture/system-flow.md`

裡面包含：
- high-level architecture
- ingestion flow
- retrieval flow
- ID strategy
- live smoke/runtime validation flow
- module responsibility map

---

## 5. ID 策略

這個系統有兩種不同層次的 ID：

### logical chunk_id
例如：
- `v1:0000`
- `smoke-ver-1:0001`

用途：
- citation
- 應用層邏輯追蹤
- payload 中保留

### Qdrant live point id
Qdrant live 需要：
- UUID，或
- unsigned integer

因此 live path 採用：
- **Qdrant-safe UUID-like point id** 作為真正的 point id
- **logical chunk_id** 仍保留在 payload

---

## 6. Query / Document Encoder 介面

### Query side
- `BaseQueryEncoder`
- `StaticQueryEncoder`
- `RuntimeQueryEncoder`
- `EncodedQuery`

Query encoder 對外統一：
- `encode(query) -> EncodedQuery`

`EncodedQuery` 包含：
- `text`
- `dense`
- `sparse`

### Document side
- `BaseDocumentEncoder`
- `StaticDocumentEncoder`
- `RuntimeDocumentEncoder`

Document encoder 對外統一：
- `encode_chunks(chunks)`

回傳每個 chunk 的：
- `dense`
- `sparse`

---

## 7. FastEmbed Runtime

### Config
使用 `FastEmbedAdapterConfig`：
- `dense_model`
- `sparse_model`
- `cache_dir`
- `threads`

### Runtime Factory
使用：
- `FastEmbedRuntimeFactory`

它會建立：
- dense model
- sparse model
- `FastEmbedRuntime`

### Runtime 能力
`FastEmbedRuntime` 提供：
- `encode_chunks(chunks)`
- `encode_query(text)`

### 預設與可選 embedding / reranker 路徑
- **預設路徑**：`FastEmbedRuntimeFactory` + `RuntimeQueryEncoder`，使用 `RAG_DENSE_MODEL` / `RAG_SPARSE_MODEL`
- **可選 embedding 路徑**：`RAG_EMBEDDING_PROVIDER=openai_compatible` 時，可改走 `HttpEmbeddingAdapter`，對本地 OpenAI-compatible `/v1/embeddings` 服務送出 `{model, input:[...]}`
- **可選 reranker 路徑**：`RAG_RERANKER_PROVIDER=http_qwen` 時，可透過 `HttpQwenReranker` 對 `/score` 服務送出 `{model, query, documents:[...]}`
- 這兩條 optional path 目前是**整合 adapter / wiring helper**，不會改變既有 FastEmbed + Qdrant 預設檢索核心

---

## 8. Ingestion Flow

### 流程順序
1. 讀入文件
2. chunking
3. 建立 `document_key`
4. 建立 `version_fingerprint`
5. 判斷 skip / new version / new document
6. document encoder 產生 dense+sparse
7. `prepare_hybrid_chunk_vectors(...)`
8. 組 payload
9. 產生 live-safe point id
10. upsert 到 Qdrant
11. 更新 DB version/document 狀態

### 相關模組
- `services/versioning.py`
- `services/ingest_pipeline.py`
- `document_encoders.py`
- `hybrid_ingest_orchestrator.py`
- `qdrant_payloads.py`
- `qdrant_hybrid_live_ops.py`

---

## 9. Retrieval Flow

### 流程順序
1. 收到 query
2. pre-retrieval
3. query encoder 產生 dense+sparse query forms
4. dense search
5. sparse search
6. fusion
7. latest-active filter
8. rerank
9. citation formatting
10. `RetrieveResponse`
11. `retrieve_tool(...)` 對外輸出

### 相關模組
- `pre_retrieval.py`
- `query_encoders.py`
- `qdrant_retriever_backend.py`
- `retrieval_fusion.py`
- `retrieval_filters.py`
- `rerank.py`
- `citation_utils.py`
- `retriever_core.py`
- `retriever_tool.py`

---

## 10. Live Hybrid Runner 使用方式

### 方式一：直接跑 module
```bash
PYTHONPATH=src python3 -m rag_ingest.live_hybrid_runner \
  --collection-name documents_live_hybrid_smoke \
  --document-id smoke-doc-1 \
  --document-key smoke:doc-1 \
  --version-id smoke-ver-1 \
  --query 'reset password' \
  --chunk 'How to reset your password using the portal.' \
  --chunk 'Contact IT support if MFA blocks the reset.'
```

### 方式二：跑 script
```bash
PYTHONPATH=src python3 scripts/run_live_hybrid.py \
  --collection-name documents_live_hybrid_smoke \
  --document-id smoke-doc-1 \
  --document-key smoke:doc-1 \
  --version-id smoke-ver-1 \
  --query 'reset password' \
  --chunk 'How to reset your password using the portal.' \
  --chunk 'Contact IT support if MFA blocks the reset.'
```

### 參數說明
- `--qdrant-url`：Qdrant URL，預設 `http://localhost:6333`
- `--collection-name`：collection 名稱
- `--dense-model`：dense model 名稱
- `--sparse-model`：sparse model 名稱
- `--cache-dir`：模型 cache 目錄
- `--threads`：encoder threads
- `--document-id`：文件 ID
- `--document-key`：文件邏輯 key
- `--version-id`：版本 ID
- `--query`：查詢文字
- `--chunk`：可重複，多個 chunk

### 預期輸出
runner 會輸出 compact JSON，包含：
- collection 設定
- point_count
- 已 upsert points 摘要
- dense_hits
- sparse_hits

---

## 11. Retriever Tool 使用方式

### Structured request
```python
request = {
    'query': 'reset password',
    'top_k': 3,
    'filters': {'source_system': 'sharepoint'},
    'rewrite_mode': 'rewrite_only',
    'history_mode': False,
    'include_debug': False,
}
```

### 呼叫方式
```python
response = retrieve_tool(request, backend=backend)
```

### 結果欄位
每筆 result 包含：
- `text`
- `score`
- `document_key`
- `version_id`
- `chunk_id`
- `metadata`
- `citation`

其中 `citation` 保留完整 trace：
- `document_key`
- `version_id`
- `chunk_id`

---

## 12. 測試

### 新增的重要測試類型
- version governance tests
- retriever contract tests
- Qdrant hybrid integration tests
- runtime wrapper tests
- live smoke helper tests
- end-to-end hybrid smoke contract tests
- live runner tests

### 執行主要測試
```bash
pytest -q
```

### GitHub Actions
Repo 包含 `.github/workflows/tests.yml`：
- Python 3.11
- 只安裝穩定 CI 子集合需要的最小依賴（`pytest`、`qdrant-client`）
- 避免預設 CI 依賴 LAN 服務、live secrets、或本機專用 runtime
- 執行 adapter / wiring / retriever contract 的穩定 pytest 子集合

如果要在本機模擬 CI：
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

---

## 13. Agno Agent Layer

目前已加入第一版 Agno-oriented agent layer building blocks：
- `AgentAnswer`
- `assemble_answer(...)`
- history-aware answer note
- `retrieve_knowledge(...)`
- `answer_query(...)`
- `format_agent_response(...)`
- `build_agno_tools(...)`
- `create_agno_specialist_agent(...)`
- `create_backend_from_env(...)`
- `run_agno_live_smoke(...)`
- `scripts/run_agno_specialist.py`

這一層的定位是 **RAG specialist agent facade / runtime wiring boundary**：
- 專做 retrieval-oriented answer assembly
- 不直接碰 Qdrant / FastEmbed 細節
- 透過既有 retriever contract 取資料
- 產生 citation-aware answer
- 透過 `agno_runtime.py` 提供可直接註冊到 Agno 的 callable tool
- 透過 `create_agno_specialist_agent(...)` 延遲載入 Agno，避免在未安裝套件的測試環境硬依賴失敗
- 透過 `agno_backend_factory.py` 從環境變數讀取最小 runtime wiring（Qdrant URL / collection / dense model / sparse model）
- 透過 `agno_live_smoke.py` 提供最小 backend → agent → response runnable path，方便在真實依賴存在時做 smoke 驗證

## 14. License

本專案採用 **MIT License**，完整條文請見 `LICENSE`。

## 15. 目前狀態

目前已完成：
- version-aware ingestion
- dense+sparse hybrid architecture
- agent-ready retriever contract
- FastEmbed runtime factory
- Qdrant live hybrid runner
- live point-id strategy fix
- end-to-end smoke contract
- 真實 live smoke 成功
- Agno-oriented agent layer foundation

目前最接近 production 的下一步：
- 補齊真實環境中的 Agno / fastembed / qdrant-client 安裝與服務可用性
- 讓 `scripts/run_agno_specialist.py` 在提供最小 env wiring 後直接走 `agno_backend_factory.py` + `agno_live_smoke.py` runnable path
- 將 live_hybrid_runner 併回正式 ingestion / retrieval 主路徑
- 建立正式 config / deployment path
- 將 hybrid fusion / rerank policy 進一步產品化
