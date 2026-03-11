# RAG Versioned Ingestion / Hybrid Retrieval System Architecture

## 1. 系統目標

這個系統的核心目標是建立一條 **版本可追蹤（version-aware）**、**可被 agent 直接使用（agent-ready）**、且支援 **Qdrant dense+sparse hybrid retrieval** 的 RAG 管線。

它解決的不是單純的「向量搜尋」，而是以下幾個問題一起處理：

- 同一份文件重複 ingest 時，避免重複 embeddings
- 文件內容更新時，保留版本歷史
- 預設只查詢最新且有效 (`is_latest=true`, `is_active=true`) 的內容
- 保留 `document_key / version_id / chunk_id`，讓 citation 可追蹤
- 讓 retriever 對 agent 保持穩定 contract，不被底層 backend 綁死
- 支援 dense + sparse 的 hybrid retrieval 路徑

---

## 2. 高層架構分層

系統分成 6 層：

### A. Source / File Ingestion Layer
負責讀取來源文件，例如本地資料夾、PDF、Office 文件、SharePoint 或未來其他來源。

主要職責：
- 讀檔
- chunking
- 建立 `document_key`
- 建立 `version_fingerprint`
- 準備 metadata

### B. Version Governance Layer
負責判斷目前文件屬於：
- 新文件
- 舊文件同版本（skip）
- 舊文件新版本（new version）

主要職責：
- document identity 管理
- current version / superseded version 狀態管理
- latest-active 規則

### C. Encoding Layer
負責把 chunk 轉成可檢索表示。

目前支援的抽象：
- query encoder
- document encoder
- static encoder
- runtime encoder
- FastEmbed runtime factory

輸出包括：
- dense vector
- sparse vector

### D. Storage / Qdrant Layer
負責將 chunk 與其 payload 寫入 Qdrant，並支援 dense/sparse retrieval。

主要職責：
- collection schema 管理
- named dense / sparse vectors
- payload index
- Qdrant-safe point id
- logical chunk_id 保留於 payload

### E. Retrieval Layer
負責完整檢索流程。

主要職責：
- pre-retrieval（rewrite / multi-query）
- vector retrieval
- sparse / keyword retrieval
- fusion
- latest-active filtering
- rerank
- citation formatting

### F. Tool / Agent Integration Layer
負責維持穩定的外部 contract，讓 agent 可直接調用。

主要職責：
- `RetrieveRequest`
- `RetrieveResponse`
- `retrieve_tool(...)`
- 保持 framework-agnostic

---

## 3. 主要模組與功能

### Version / Governance
- `contracts.py`：document key / version fingerprint 基本規則
- `services/versioning.py`：new document / skip / new version 決策
- `db/models.py`：`Document`, `DocumentVersion`, `IngestionJob`
- `jobs/nightly_cleanup.py`：清除已失效舊版本
- `jobs/reconcile_counts.py`：對帳 DB 與 Qdrant point 數量

### Ingestion
- `services/ingest_pipeline.py`：版本建立、payload 建立、Qdrant upsert
- `hybrid_ingest_orchestrator.py`：把 document encoder 輸出拆成 dense/sparse
- `live_smoke.py`：retrieval smoke payload / helper

### Agno Runtime Wiring
- `agno_backend_factory.py`：從 env/config 讀取最小 live wiring，建立 Qdrant + runtime-backed retriever backend
- `agno_runtime.py`：建立 Agno tools 與 specialist agent
- `agno_live_smoke.py`：最小 backend → agent → response smoke 路徑
- `scripts/run_agno_specialist.py`：CLI entrypoint；缺設定時應明確失敗，設定齊全時可走最小 runnable path

### Encoding
- `query_encoders.py`：`BaseQueryEncoder`, `StaticQueryEncoder`, `RuntimeQueryEncoder`
- `document_encoders.py`：`BaseDocumentEncoder`, `StaticDocumentEncoder`, `RuntimeDocumentEncoder`
- `fastembed_adapters.py`：FastEmbed config / runtime factory / runtime wrapper
- `sparse_vectors.py`：sparse vector shape helper

### Qdrant Integration
- `qdrant_integration.py`：collection definition / payload index fields
- `qdrant_payloads.py`：payload 與 point id helper
- `qdrant_hybrid_live_ops.py`：hybrid point struct
- `qdrant_retriever_backend.py`：Qdrant hit → retriever candidate
- `live_hybrid_runner.py`：真實 live encode → upsert → query runner

### Retrieval
- `pre_retrieval.py`：rewrite / multi-query
- `retrieval_fusion.py`：RRF fusion
- `retrieval_filters.py`：latest-active filter / history mode
- `rerank.py`：rerank abstraction
- `citation_utils.py`：citation 組裝
- `retriever_schemas.py`：request/response schema
- `retriever_core.py`：retrieve pipeline 核心
- `retriever_tool.py`：tool-style entrypoint

---

## 4. ID 與追蹤策略

系統中有三種重要識別：

### document_key
代表文件邏輯身分，例如：
- `sharepoint:SOP-001`
- `localfs:/docs/policy.md`

### version_id
代表文件版本身分。
每次新版本建立時都會有新的 `version_id`。

### chunk_id
代表邏輯上的 chunk 身分，例如：
- `v1:0000`
- `smoke-ver-1:0001`

### Qdrant point id
這個和 `chunk_id` 不同。

Qdrant live 實測確認 point id 需要：
- UUID，或
- unsigned integer

因此現在策略是：
- **Qdrant point id**：使用 Qdrant-safe UUID-like id
- **logical chunk_id**：保存在 payload 中

這樣既符合 Qdrant 限制，也保留應用層追蹤能力。

---

## 5. 系統流程順序

### Ingestion Path
1. 讀入文件
2. chunking
3. 建立 `document_key`
4. 建立 `version_fingerprint`
5. 判斷 skip / new version / new document
6. document encoder 產生 dense+sparse
7. 組成 payload
8. 以 Qdrant-safe point id 寫入 Qdrant
9. 更新 DB version/document 狀態

### Retrieval Path
1. 收到 query
2. pre-retrieval（rewrite / multi-query）
3. query encoder 產生 dense+sparse query forms
4. Qdrant dense search
5. Qdrant sparse search
6. fusion
7. latest-active filtering
8. rerank
9. citation formatting
10. tool response output

---

## 6. Error Handling / Safety 策略

### Skip instead of duplicate
若 `document_key + version_fingerprint` 相同，直接 skip，不重建 embeddings。

### Supersede instead of overwrite
若是同 document_key 的新版本：
- 舊版本標記為 superseded / inactive
- 新版本成為 current version

### latest-active default
正常 retrieval 預設只查：
- `is_latest = true`
- `is_active = true`

### history mode
若需要查歷史版本，才顯式打開 `history_mode`。

### Reconciliation / cleanup
- cleanup：刪掉 오래 inactive 的 superseded chunks
- reconcile：對帳 DB / Qdrant active chunk counts

---

## 7. 測試策略

測試分成 4 類：

### A. Unit tests
驗證 schema、payload、filter、fusion、rerank、encoder abstraction。

### B. Contract tests
驗證：
- retriever contract
- tool output shape
- backend adapter shape
- live point id strategy

### C. Integration tests
驗證：
- ingest + version governance
- dense+sparse pipeline
- runtime wrapper 到 backend adapter 的整合

### D. Smoke tests
驗證：
- end-to-end fake runtime smoke
- live FastEmbed + live Qdrant smoke

---

## 8. Agno Agent Layer

在 RAG core 之上，現已加入一層輕量的 Agno-oriented agent foundation：

- `AgentAnswer`：agent answer schema
- `assemble_answer(...)`：retrieval result -> answer assembly
- `retrieve_knowledge(...)`：retriever tool adapter
- `answer_query(...)`：specialist agent facade
- `format_agent_response(...)`：user-facing formatter
- `agno_runtime.py`：Agno runtime wiring helper
- `build_agno_tools(...)`：建立可直接註冊到 Agno 的 retrieval callable
- `create_agno_specialist_agent(...)`：lazy-import Agno `Agent` 並註冊 tools
- `scripts/run_agno_specialist.py`：最小 runnable entrypoint stub

這一層目前仍是 framework-light facade，主要目的是：
- 維持底層 RAG core 不被 agent framework 綁死
- 先建立 citation-aware answer path
- 透過 `build_agno_tools(...)` 讓現有 retriever contract 可直接掛進 Agno tool registry
- 透過 lazy import 讓未安裝 Agno 的 test/runtime 邊界仍可清楚失敗

## 9. 當前狀態

目前系統已完成：
- version-aware ingestion
- agent-ready retriever contract
- dense+sparse hybrid architecture
- runtime encoder abstraction
- Qdrant backend adapter
- live runner / smoke path
- live Qdrant + FastEmbed 最小驗證
- Agno-oriented agent layer foundation

目前最接近產品化的下一步是：
- 把 Agno facade 接到真正的 Agno runtime / tool registration
- 把 live runner 併回正式 ingestion / retrieval 主路徑
- 建立更正式的 production config
- 將 hybrid fusion / rerank policy 做成可調參數
