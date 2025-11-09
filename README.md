# 🚀 BMC API Reliability & Performance Validation (VQE Framework)

[![Test Coverage Report](https://img.shields.io/badge/coverage-100%25-brightgreen)](https://github.com/hiraeth92/BMC-API-Reliability-Test)
![Coverage](https://img.shields.io/badge/Coverage-Auto--Generated-brightgreen?style=flat-square&logo=codecov)

---

## 📌 專案簡介

本專案為伺服器 **BMC（Baseboard Management Controller）API** 的 **VQE（Vendor Quality Engineering）自動化驗證框架**，透過高併發壓力測試與統計分析，驗證 API 的可靠度 (Reliability) 與效能穩定性 (Performance Stability)。  

核心特色：
- 模擬多用戶併發存取 BMC API，測試可靠性與穩定性  
- 自動量測平均延遲、標準差、P95 延遲  
- 錯誤追蹤與日誌記錄，可區分軟體錯誤與硬體錯誤  
- CI/CD 自動化測試與報告生成，支援 GitHub Actions

---

## 🎯 專案目標

- ✅ 高併發壓力測試，模擬實際伺服器負載  
- ✅ 可靠度驗證：所有請求皆成功 (HTTP 200)  
- ✅ 效能驗證：平均延遲、標準差、P95 延遲自動統計  
- ✅ 自動化 CI/CD 流程，生成可視化測試報告  
- ✅ 適用於伺服器製造商 VQE 團隊進行 API 健全性驗證

---

## 🧪 使用技術

| 類別        | 技術/工具                                  |
|-------------|--------------------------------------------|
| 語言        | Python 3.10 / 3.11                         |
| 測試框架    | pytest, requests                            |
| 並行工具    | concurrent.futures (ThreadPoolExecutor)     |
| CI/CD       | GitHub Actions                              |
| 日誌系統    | Logging + UTF-8 File Handler               |
| 效能統計    | Mean / Std / P95 延遲                       |

---

## 📂 專案目錄結構
```
BMC-API-Reliability-Test/
├── test_reliability.py       # 核心測試邏輯 (pytest + requests)
├── .github/workflows/
│   └── ci.yml                # GitHub Actions CI/CD 工作流程
├── reliability_errors.log    # 測試日誌 (自動產生)
└── README.md
```
---

## 🔄 自動化流程設計（CI/CD）

每次推送或發出 Pull Request，GitHub Actions 將自動執行：

1. 安裝依賴套件 (`pip install -r requirements.txt`)  
2. 執行 pytest 自動化測試  
3. 生成 JUnit XML 測試報告  
4. 上傳報告 Artifact 並輸出可靠度與效能統計

流程檔案：  

.github/workflows/ci.yml

---

## 🧾 測試案例（test_reliability.py）

### ✅ Reliability Test
確保所有 API 請求皆返回 `HTTP 200`：
```bash
pytest -v -s test_reliability.py::TestApiReliability::test_reliability_zero_error_rate

⚡ Performance Test

驗證平均延遲是否低於 2000ms：

pytest -v -s test_reliability.py::TestApiReliability::test_performance_statistics_analysis


⸻

📊 測試報告範例

--- 效能統計數據報告 ---
目標 API: https://www.google.com/robots.txt
併發請求數: 50
平均延遲 (Avg Latency): 1313.52 ms
標準差 (Std Dev): 122.38 ms
P95 延遲: 1648.90 ms
效能閾值: 2000 ms
✅ 效能測試通過


⸻

🧩 後續擴充建議
	•	支援多端點自動輪測 (URL Pool)
	•	壓力曲線可視化 (Matplotlib / Grafana)
	•	自動報告推送至 Slack / Teams

⸻

🙋‍♂️ 作者資訊
	•	GitHub: @hiraeth92￼
	•	Email: bossun113@gmail.com￼

本專案作為伺服器 API 壓力與可靠性測試示範，展示 CI/CD 自動化與效能統計分析實作。