# 這是伺服器 BMC API 的 VQE（Vendor Quality Engineering）驗證框架。
# 我們的目標是確保 API 在高併發壓力下，既可靠（沒有錯誤）又高效（速度快）。

import requests # 用來發送 HTTP 請求給目標 API。
import concurrent.futures # 用來實現併發，模擬多個使用者同時存取 API。
import time # 用來計算每個請求的延遲時間（延遲是效能的關鍵指標）。
import pytest # 這是我們的測試框架，負責執行和組織所有測試案例。
import logging # 這是 Log 記錄模組，負責追蹤錯誤和輸出詳細的效能報告。
import statistics # 用來計算平均值和標準差等統計數據。
import os # 用來處理檔案路徑，確保日誌檔案能被正確存取。
import atexit # 引入這個模組，確保 Python 程式結束時，我們可以做一些清理工作，例如關閉 Log 檔案。

# --- VQE Log 配置：專為問題追蹤設計 ---
# 這是 Log 系統的核心配置，確保無論測試環境多複雜（例如在 Pytest 或 Windows），
# 我們的錯誤追蹤和報告都能正常運作。

# 1. 定義 Log 檔案路徑
# 我們將 Log 檔案放在系統的暫存目錄 (%TEMP%)，避免 OneDrive 鎖定等問題。
LOG_FILENAME = os.path.join(os.environ['TEMP'], 'reliability_errors.log')
if os.path.exists(LOG_FILENAME):
    os.remove(LOG_FILENAME)  # 每次運行前，先清除舊的 Log 檔案，確保報告是最新一輪的。

# 2. 取得 Root Logger
logger = logging.getLogger()
logger.setLevel(logging.INFO) # 設置 Logger 的最低等級為 INFO，確保所有資訊性報告都能被記錄下來。

# 3. 定義 Log 格式
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# 4. 手動創建 StreamHandler (輸出到終端機/PyCharm Console)
# 確保測試運行時，數據能在螢幕上即時顯示。
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# 5. 手動創建 FileHandler (輸出到檔案，這是我們正式的 VQE 報告)
# 這是最關鍵的部分。我們強制指定 'utf-8' 編碼來避免 Windows 環境下中文字和特殊符號 (✅) 造成的編碼錯誤。
file_handler = logging.FileHandler(LOG_FILENAME, mode='a', encoding='utf-8')
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO) # 顯式設置 FileHandler 必須處理 INFO 訊息。
logger.addHandler(file_handler)

# 6. 輸出絕對路徑並註冊清理函數
# 告訴使用者 Log 檔案確切位置，方便追溯。
logger.info(f"【日誌追溯路徑】詳細報告已寫入檔案: {LOG_FILENAME}")

def cleanup_logging():
    """確保程式退出時，Log 檔案被安全關閉和釋放，避免數據遺失。"""
    try:
        # 檢查我們的手動 FileHandler 是否還在 Log 列表中
        if file_handler in logger.handlers:
            file_handler.close() # 關閉檔案，確保所有緩衝區數據寫入硬碟。
            logger.removeHandler(file_handler)
    except Exception as e:
        # 如果清理過程中出現問題，就印出來，但不會影響測試結果。
        print(f"Log 清理發生錯誤: {e}")

# 註冊清理函數：保證在整個 Python 程式運行結束時，自動執行 cleanup_logging。
atexit.register(cleanup_logging)


# ---- VQE 測試標準配置 (可根據需求調整) ----
NUM_REQUESTS = 50  # 併發請求數量：我們模擬 50 個使用者同時訪問 API。

# 【優化目標】這裡設定我們要測試的 API 端點。
TARGET_URL = "https://www.google.com/robots.txt"

# 【調整閾值】這是性能的驗收標準。平均延遲必須小於這個毫秒數 (2000 ms = 2 秒)。
LATENCY_THRESHOLD_MS = 2000  # 效能閾值：這是通過測試的最低要求。


class TestApiReliability:
    """
    這是 Pytest 的測試類別。所有與 BMC API 可靠度和效能相關的測試案例都在這裡。
    """

    def send_request(self, url):
        """
        核心工作函數：發送單一請求，並精確計時和追蹤錯誤類型。
        它返回 (HTTP 狀態碼, 延遲時間)。
        """
        start_time = time.time()
        try:
            # 設置連線超時，如果超過 5 秒沒有回應，就視為失敗。
            response = requests.get(url, timeout=5)
            latency_ms = (time.time() - start_time) * 1000 # 將秒轉換為毫秒

            if response.status_code != 200:
                # 軟體錯誤：API 內部邏輯錯誤 (例如 404, 500 等)
                logger.error(f"【追蹤碼】請求 {url} 返回非 200 狀態碼: {response.status_code}")
                return response.status_code, latency_ms

            return response.status_code, latency_ms # 成功時返回 200 和延遲時間

        except requests.exceptions.RequestException as e:
            # 硬體錯誤追蹤：網路連線、超時或 DNS 等外部問題
            error_type = type(e).__name__
            error_message = f"【硬體錯誤追蹤】請求 {url} 發生連線異常: {error_type}, 原因: {str(e)}"
            logger.error(error_message)
            return 500, (time.time() - start_time) * 1000 # 將所有硬體錯誤視為 500 處理

    @pytest.fixture(scope="class")
    def concurrent_test_results(self):
        """
        Pytest 夾具 (Fixture)：在所有測試案例開始前，只執行一次壓力測試。
        它使用執行緒池來併發發送所有請求，並收集結果。
        """
        all_results = []
        logger.info(f"--- 開始 {NUM_REQUESTS} 併發可靠度測試 (目標: {TARGET_URL}) ---")

        # 創建執行緒池，限制最多 20 個工作執行緒
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            # 提交所有 50 個請求到執行緒池
            future_to_url = [executor.submit(self.send_request, TARGET_URL) for _ in range(NUM_REQUESTS)]

            # 等待所有請求完成，並收集結果 (狀態碼, 延遲)
            for future in concurrent.futures.as_completed(future_to_url):
                all_results.append(future.result())

        logger.info("--- 併發測試完成 ---")
        return all_results # 將這個結果列表傳遞給接下來的所有測試函數。

    # ------------------ VQE 驗證點 1：可靠度 (Reliability) ------------------
    def test_reliability_zero_error_rate(self, concurrent_test_results):
        """
        第一個測試：驗證可靠度，要求 API 必須達到 100% 成功率 (0% 錯誤率)。
        這檢查的是 API 的功能是否正常運作。
        """
        # 過濾出所有非 200 狀態碼的失敗請求
        failed_requests = [code for code, latency in concurrent_test_results if code != 200]
        logger.info(f"總請求數: {NUM_REQUESTS}, 失敗數: {len(failed_requests)}")

        # 斷言：如果失敗數不等於 0，測試就失敗。
        assert len(failed_requests) == 0, \
            f"❌ 可靠度測試失敗：有 {len(failed_requests)} 次請求未成功 (非 200 狀態碼)。請查閱 Log 追蹤。"

        logger.info("✅ 可靠度測試通過：錯誤率為 0%。")

    # ------------------ VQE 驗證點 2：效能統計分析 (Performance Statistics) ------------------
    def test_performance_statistics_analysis(self, concurrent_test_results):
        """
        第二個測試：驗證效能，檢查 API 響應速度是否符合標準。
        這裡我們使用多種統計指標來評估 API 的穩定性。
        """
        # 僅使用成功的請求來計算延遲，避免失敗的請求干擾性能指標。
        successful_latencies = [latency for code, latency in concurrent_test_results if code == 200]

        if len(successful_latencies) < 2:
            pytest.skip("成功請求數不足，無法進行統計分析。")

        # 計算平均延遲 (Avg Latency)
        average_latency = statistics.mean(successful_latencies)
        # 計算標準差 (Std Dev)，這是 VQE 衡量 API 穩定性的重要指標，越低越好。
        std_dev_latency = statistics.stdev(successful_latencies)

        # 計算 P95 延遲：表示 95% 的請求都在這個時間內完成，這是比平均值更嚴苛的指標。
        successful_latencies.sort()
        p95_index = min(len(successful_latencies) - 1, int(len(successful_latencies) * 0.95))
        p95_latency = successful_latencies[p95_index]

        # 將詳細的統計數據輸出到 Log 和 Console 中
        logger.info("--- 效能統計數據報告 ---")
        logger.info(f"目標 API: {TARGET_URL}")
        logger.info(f"併發請求數: {NUM_REQUESTS}")
        logger.info(f"平均延遲 (Avg Latency): {average_latency:.2f} ms")
        logger.info(f"標準差 (Std Dev): {std_dev_latency:.2f} ms (VQE 穩定性指標)")
        logger.info(f"P95 延遲: {p95_latency:.2f} ms")
        logger.info(f"效能閾值 (Threshold): {LATENCY_THRESHOLD_MS} ms")
        logger.info("---------------------------")

        # 核心斷言：檢查平均延遲是否低於我們設定的效能閾值。
        assert average_latency < LATENCY_THRESHOLD_MS, \
            f"❌ 效能測試失敗：平均延遲 {average_latency:.2f} ms，已超過閾值 {LATENCY_THRESHOLD_MS} ms。"

        logger.info(f"✅ 效能測試通過：平均延遲低於 {LATENCY_THRESHOLD_MS} ms。")

        # --- 最終 Log 處理 ---
        # 確保在測試運行結束前，將所有日誌訊息從緩衝區寫入檔案，避免數據遺失。
        for handler in logger.handlers:
            handler.flush()
