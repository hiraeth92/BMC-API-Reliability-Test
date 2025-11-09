# 🔧 BMC API Reliability & Performance Validation (VQE Framework)

本專案為伺服器 **BMC（Baseboard Management Controller）API** 的  
**VQE（Vendor Quality Engineering）自動化驗證框架**。  
透過高併發壓力測試與統計分析，驗證 API 的 **可靠度 (Reliability)** 與 **效能穩定性 (Performance Stability)**。

---

## 🎯 專案目標

- 模擬多用戶併發存取 BMC API，驗證穩定性與錯誤率  
- 量測延遲時間、成功率與 P95 延遲 (95th Percentile)  
- 自動化整合至 GitHub Actions，於 CI 中執行 VQE 測試  
- 協助伺服器製造商與驗證工程團隊快速檢測 API 健全度  

---

## 🧩 專案架構
```
BMC-API-Reliability-Test/
├── test_reliability.py        # 核心測試邏輯 (pytest + requests)
├── .github/
│   └── workflows/
│       └── ci.yml             # GitHub Actions 工作流程
├── reliability_errors.log     # 測試日誌 (自動產生)
└── README.md
```
---

## ⚙️ 主要功能

| 功能模組 | 說明 |
|-----------|------|
| 🧵 **高併發壓力測試** | 使用 `ThreadPoolExecutor` 模擬多用戶同時發送 API 請求 |
| ✅ **可靠度驗證 (Reliability Test)** | 要求所有請求返回 HTTP 200，確保 0% 錯誤率 |
| ⚡ **效能統計分析 (Performance Test)** | 計算平均延遲、標準差、P95 延遲與穩定性指標 |
| 🧠 **跨平台日誌系統** | 使用 `tempfile` + `logging` 確保 Linux / Windows / CI 皆能正確寫入 |
| ☁️ **GitHub Actions 整合** | 自動化執行測試與報告上傳 (JUnit XML 格式) |

---

## 🧠 技術要點

- **語言**：Python 3.10 / 3.11  
- **框架**：Pytest、Requests、Concurrent Futures  
- **自動化**：GitHub Actions  
- **紀錄系統**：Logging + UTF-8 File Handler  
- **統計模組**：Mean / Std / P95 Latency  
- **錯誤追蹤**：區分軟體錯誤 (非 200) 與硬體錯誤 (Timeout / DNS)

---

## 🧾 測試項目範例

### ✅ 可靠度測試 (Reliability Test)
確保所有 API 請求皆返回 `HTTP 200`：
```bash
pytest -v -s test_reliability.py::TestApiReliability::test_reliability_zero_error_rate

⚡ 效能測試 (Performance Test)

驗證平均延遲是否低於設定閾值 (預設 2000ms)：

pytest -v -s test_reliability.py::TestApiReliability::test_performance_statistics_analysis


⸻

🔄 GitHub Actions 自動化流程

當程式碼推送 (push) 或發出 Pull Request 時，自動執行以下步驟：
	1.	在 Python 3.10 / 3.11 上平行測試
	2.	安裝依賴並執行 pytest
	3.	生成 JUnit XML 測試報告
	4.	上傳 Artifact 並於 CI 界面顯示結果

📂 工作流程檔案：

.github/workflows/ci.yml


⸻

📊 測試報告範例 (CI Log 範例)

--- 效能統計數據報告 ---
目標 API: https://www.google.com/robots.txt
併發請求數: 50
平均延遲 (Avg Latency): 113.52 ms
標準差 (Std Dev): 22.38 ms (VQE 穩定性指標)
P95 延遲: 148.90 ms
效能閾值 (Threshold): 2000 ms
✅ 效能測試通過


⸻

🔍 未來可擴充方向
	•	支援多端點自動輪測 (URL Pool)
	•	整合壓力曲線可視化輸出 (Matplotlib / Grafana)
	•	自動報告上傳至 Slack / Teams
	•	增加錯誤分類統計與 API 響應驗證內容

⸻

👤 作者

Hiraeth92
📍 GitHub 專案連結：BMC API Reliability Test￼