# NEXT_STEPS.md

# RAG_Agno_pipeline — Next Steps

這份文件整理目前專案從「已可運行」走向「更完整可交付 / 可維運 / 可上線」的下一步。

---

## 目前狀態摘要

目前已具備：
- version-aware ingestion
- dense + sparse hybrid retrieval
- Qdrant live path
- Agno specialist agent wiring
- LAN HTTP embedding service integration
- LAN HTTP reranker service integration
- live smoke 已跑通
- GitHub repo 已建立並推送（workflow 檔暫未推）

目前尚未完全補齊：
- CI workflow 正式上 GitHub
- production-grade fallback / timeout 策略
- 更完整的 deployment / operations 文件
- 更成熟的 ingestion 入口與日常操作流程

---

# 1. Must-have（優先補）

這些是最值得優先完成的項目，補完之後，專案會更像一個「可交付工程」，而不只是技術驗證成果。

## 1.1 補回 GitHub Actions workflow

### 目的
建立基本 CI，確保每次 push / PR 都能自動驗證。

### 內容
- 補回 `.github/workflows/tests.yml`
- 使用 Python 3.11
- 跑一組穩定的 pytest subset
- 避免依賴 secrets 的 live 測試進入預設 CI

### 成功標準
- PR / push 時自動跑測試
- 不依賴本地私有 LAN 服務
- workflow 在 GitHub 顯示綠燈

---

## 1.2 整理 `.env.example` 與設定文件

### 目的
讓其他人或未來自己可以快速理解有哪些設定路徑可切換。

### 內容
至少清楚區分：
- FastEmbed dense path
- OpenAI-compatible HTTP embedding path
- BM25 sparse path
- HTTP Qwen reranker path
- Agno model path
- Qdrant path

### 建議補充
- 哪些是必要設定
- 哪些是 optional
- 預設 fallback 行為是什麼

### 成功標準
- 新使用者可只看 `.env.example` + README 就完成最小啟動

---

## 1.3 補完整 Quick Start

### 目的
讓 repo 首頁能真正支援「第一次進來就能跑」。

### 內容
README 應補強為：
1. 安裝依賴
2. 啟動 Qdrant
3. 設定 `.env`
4. 跑 retrieval smoke
5. 跑 Agno specialist smoke
6. 切換到 LAN embedding / reranker 路徑

### 成功標準
- 新人或未來自己不需要翻大量程式就能執行

---

## 1.4 Fallback / timeout 策略

### 目的
把目前可跑的系統，提升成更耐用的系統。

### 建議補的 fallback
- embedding service timeout → fallback 到 FastEmbed dense
- reranker timeout / 400 / 500 → fallback 到 lightweight rerank 或直接跳過 rerank
- Agno model 失敗 → 提供清楚錯誤訊息或 fallback model path

### 成功標準
- 外部服務短暫故障時，不會整條 retrieval path 直接失效

---

## 1.5 補回 workflow 權限後推上 CI 檔

### 目的
把本地已做好的工程衛生真正同步到 GitHub。

### 內容
- 使用有 `workflow` scope 的 PAT 或正確 GitHub 認證
- 推送 `.github/workflows/tests.yml`

### 成功標準
- GitHub repo 上看得到 CI workflow
- push / PR 會自動驗證

---

# 2. Should-have（第二層優先）

這些項目不是最急，但會顯著提升專案的可維護性與產品化程度。

## 2.1 正式 ingestion CLI / command

### 目的
讓 ingest 不再只是 scattered scripts / smoke path，而是有固定入口。

### 可能內容
例如：
- `scripts/ingest_documents.py`
- `scripts/reindex_collection.py`
- `scripts/check_retrieval.py`

### 成功標準
- 使用者可透過標準命令完成 ingest / re-ingest / smoke

---

## 2.2 Retrieval / rerank policy 明文化

### 目的
讓模型切換與排序策略可解釋、可調整。

### 建議補充
- top_k before rerank
- final top_k after rerank
- 何時跳過 rerank
- 何時啟用 history mode
- 何時使用 rewrite / multi-query

### 成功標準
- retrieval 行為不是埋在程式裡的隱性規則

---

## 2.3 Observability / logging

### 目的
讓未來 debug 與效能觀察更容易。

### 建議加入
- request id / trace id
- query latency
- embedding latency
- reranker latency
- vector / keyword / fused / reranked candidate counts
- optional debug mode

### 成功標準
- 問題出現時可快速定位是 embedding、Qdrant、reranker、還是 LLM 出錯

---

## 2.4 Deployment / operations runbook

### 目的
把知識從「腦中知道」變成「文件化可操作」。

### 應補內容
- 服務相依清單
- LAN embedding service 驗證方式
- LAN reranker 驗證方式
- Qdrant 健康檢查方式
- Agno model 設定方式
- 常見錯誤與排除方法

### 成功標準
- 服務掛掉時，照文件就能快速檢查

---

# 3. Nice-to-have（加分項）

這些不是短期必需，但做好會讓專案更成熟。

## 3.1 更完整的來源接入
- PDF / Office / local folder 之外的來源接入
- API / database / wiki / cloud docs

## 3.2 更細緻的 citation 呈現
- 顯示 chunk 內容摘錄
- 顯示版本資訊
- 顯示文件標題而不只是 document_key

## 3.3 多模型策略
- OpenAI / local model / fallback model 切換
- 根據成本或延遲選模型

## 3.4 管理後台 / dashboard
- 查 collection 狀態
- 查版本狀態
- 查 ingestion job 結果
- 查 retrieval log

## 3.5 更完整的 benchmark / eval
- 檢索品質評估
- reranker 效果比較
- FastEmbed vs HTTP embedding 比較
- latency / cost / stability 比較

---

# 4. 推薦優先順序

如果要我建議最合理的下一輪順序：

## Phase 1 — 專案衛生
1. 補回 GitHub Actions workflow
2. 補強 `.env.example`
3. 補完整 README Quick Start

## Phase 2 — 穩定性
4. 補 fallback / timeout 策略
5. 補 logging / observability
6. 補 operations runbook

## Phase 3 — 使用性
7. 建正式 ingestion CLI
8. 建 retrieval / rerank policy config
9. 強化 deployment 文件

## Phase 4 — 產品化
10. 做 benchmark / eval
11. 擴充更多來源接入
12. 若需要，再做 dashboard / admin tooling

---

# 5. 上線前 Checklist

## 功能
- [ ] ingestion 路徑可穩定重跑
- [ ] retrieval path 穩定
- [ ] citation 正確
- [ ] reranker 可用且可 fallback
- [ ] Agno specialist 可穩定回覆

## 設定
- [ ] `.env.example` 與 README 一致
- [ ] secrets 不落地到 repo
- [ ] Qdrant / embedding / reranker / model 設定清楚

## 品質
- [ ] CI 可跑
- [ ] 測試通過
- [ ] live smoke 可重現

## 維運
- [ ] runbook 存在
- [ ] 錯誤排障路徑清楚
- [ ] timeout / fallback 策略已定義

---

# 6. 一句話總結

這個專案現在**核心功能已經成立**，下一步最該補的不是再發明新功能，而是把：

- CI
- config
- README / runbook
- fallback
- operations

這些「工程衛生與產品化能力」補齊。
