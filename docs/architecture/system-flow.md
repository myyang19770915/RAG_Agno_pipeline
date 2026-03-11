# System Flow (Mermaid)

## 1. High-Level Architecture

```mermaid
flowchart TD
    A[Source Files / External Content] --> B[Chunking + Metadata Preparation]
    B --> C[Version Governance]
    C -->|skip| C1[No Re-embedding]
    C -->|new doc / new version| D[Document Encoder Layer]
    D --> E[Hybrid Ingest Orchestrator]
    E --> F[Qdrant Hybrid Storage]
    F --> G[Retriever Core]
    G --> H[Tool / Agent Interface]

    I[User / Agent Query] --> J[Pre-Retrieval]
    J --> K[Query Encoder Layer]
    K --> G
```

## 2. Ingestion Flow

```mermaid
flowchart TD
    A[Input Document] --> B[Build document_key]
    B --> C[Build version_fingerprint]
    C --> D{Version Decision}
    D -->|same doc + same fingerprint| E[Skip]
    D -->|new document| F[Create Document + Version]
    D -->|same document + new fingerprint| G[Create New Version and Supersede Old]

    F --> H[Chunk Document]
    G --> H
    H --> I[RuntimeDocumentEncoder / StaticDocumentEncoder]
    I --> J[Dense + Sparse Encodings]
    J --> K[prepare_hybrid_chunk_vectors]
    K --> L[build_payload + logical chunk_id]
    L --> M[Generate Qdrant-safe point_id]
    M --> N[Upsert to Qdrant]
    N --> O[Update DB state]
```

## 3. Retrieval Flow

```mermaid
flowchart TD
    A[Incoming Query] --> B[RetrieveRequest]
    B --> C[Pre-retrieval]
    C --> D[rewrite / multi-query / normalization]
    D --> E[RuntimeQueryEncoder / StaticQueryEncoder]
    E --> F[EncodedQuery dense+sparse]
    F --> G[Qdrant dense search]
    F --> H[Qdrant sparse search]
    G --> I[Fusion]
    H --> I
    I --> J[latest-active filter]
    J --> K[Rerank]
    K --> L[Format citation + RetrieveResult]
    L --> M[RetrieveResponse]
    M --> N[retrieve_tool / Agent Adapter]
    N --> O[build_agno_tools / create_agno_specialist_agent]
    O --> P[create_backend_from_env / run_agno_live_smoke]
```

## 4. ID Strategy

```mermaid
flowchart LR
    A[version_id + chunk_index] --> B[logical chunk_id]
    B -->|stored in payload| C[payload.chunk_id]

    A --> D[build_qdrant_point_id]
    D --> E[Qdrant-safe UUID-like point_id]
    E --> F[Qdrant PointStruct.id]
```

## 5. Live Smoke / Runtime Validation Flow

```mermaid
flowchart TD
    A[CLI / script run_live_hybrid] --> B[FastEmbedRuntimeFactory]
    B --> C[FastEmbedRuntime]
    C --> D[encode_chunks]
    C --> E[encode_query]
    D --> F[LiveHybridQdrantOps.ensure_collection]
    F --> G[Upsert hybrid points]
    E --> H[Dense Query]
    E --> I[Sparse Query]
    G --> H
    G --> I
    H --> J[Dense Hits Summary]
    I --> K[Sparse Hits Summary]
    J --> L[Compact JSON Output]
    K --> L
```

## 6. Module Responsibility Map

```mermaid
flowchart TD
    A[contracts.py / versioning.py] --> A1[Document Identity + Version Rules]
    B[document_encoders.py / query_encoders.py] --> B1[Encoding Abstraction]
    C[fastembed_adapters.py] --> C1[Real Runtime Factory]
    D[services/ingest_pipeline.py] --> D1[Write Path]
    E[qdrant_integration.py / qdrant_payloads.py] --> E1[Collection + Payload Contract]
    F[qdrant_retriever_backend.py] --> F1[Qdrant Result Adapter]
    G[retriever_core.py] --> G1[Fusion + Filter + Rerank Pipeline]
    H[retriever_tool.py] --> H1[Agent-facing Structured Contract]
    I[live_hybrid_runner.py] --> I1[Runnable Live Validation Path]
```

## 7. Deployment / Runtime Topology

```mermaid
flowchart LR
    U[User / Agent / Tool Caller]
    A[Agno Specialist Facade\nanswer_query]
    AR[Agno Runtime Wiring\nbuild_agno_tools / create_agno_specialist_agent]
    AB[Backend Factory\ncreate_backend_from_env]
    AS[Agno Live Smoke\nrun_agno_live_smoke]
    TA[retrieve_knowledge\nAgno Tool Adapter]
    T[retrieve_tool\nStructured Contract]
    R[retriever_core\npre-retrieval + fusion + rerank]
    QB[qdrant_retriever_backend\nDense/Sparse Query Adapter]
    QE[RuntimeQueryEncoder]
    DE[RuntimeDocumentEncoder]
    FE[FastEmbedRuntimeFactory / FastEmbedRuntime]
    HI[hybrid_ingest_orchestrator]
    IP[ingest_pipeline\nversion-aware upsert]
    DB[(Metadata DB\nDocument / Version State)]
    Q[(Qdrant\nDense + Sparse Vectors\nPayload Indexes)]
    SRC[Source Files / External Docs]
    SM[live_hybrid_runner / smoke path]

    U --> A
    U --> AR
    U --> AS
    AR --> AB
    AB --> QB
    A --> TA
    AR --> TA
    AS --> AB
    AS --> AR
    TA --> T
    T --> R
    R --> QE
    QE --> FE
    R --> QB
    QB --> Q
    QB --> R

    SRC --> DE
    DE --> FE
    DE --> HI
    HI --> IP
    IP --> DB
    IP --> Q

    SM --> FE
    SM --> Q
    SM --> IP
```

### Topology Explanation
- **User / Agent / Tool Caller**：最上層呼叫端，可能是 agent、CLI、或其他 service。
- **answer_query / Agno Specialist Facade**：Agno-oriented specialist entrypoint，負責把 retrieval 結果組裝成 citation-aware answer。
- **build_agno_tools / create_agno_specialist_agent**：Agno runtime wiring layer，提供 tool registration 與 lazy-import Agent 建立點。
- **create_backend_from_env**：從環境變數讀取最小 live wiring，建立 runtime-backed retriever backend。
- **run_agno_live_smoke**：把 backend factory、agent factory、query 執行串成最小可測 runnable path。
- **retrieve_knowledge**：Agno tool adapter，負責把 agent 請求轉成 retriever tool 呼叫。
- **retrieve_tool**：對外穩定入口，維持固定 request / response schema。
- **retriever_core**：負責 query rewrite、fusion、filter、rerank 與結果格式化。
- **RuntimeQueryEncoder / RuntimeDocumentEncoder**：把真實 runtime 包成統一介面。
- **FastEmbedRuntime**：提供 dense / sparse 真實編碼能力。
- **qdrant_retriever_backend**：把 Qdrant live query 結果轉成 retriever candidate。
- **ingest_pipeline**：負責版本判斷、payload 建立、Qdrant upsert。
- **Metadata DB**：保存 document 與 version 狀態。
- **Qdrant**：保存 dense+sparse 向量與 payload，支援 live retrieval。
- **live_hybrid_runner / smoke path**：獨立的真實環境驗證路徑，用於快速檢查整條 live path 是否正常。
