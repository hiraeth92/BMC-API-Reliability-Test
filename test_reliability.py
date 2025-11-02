# VQE API 可靠度與效能驗證框架 (跨平台日誌修正)

import requests
import concurrent.futures
import time
import statistics
import logging
import os
import tempfile  # 確保此模組被導入
import atexit
import sys

# --- I. 日誌配置 (確保測試結果被永久記錄) ---

# 設置日誌檔案的路徑：使用 tempfile.gettempdir() 確保跨平台兼容性
# Linux/Ubuntu: 會解析為 /tmp/...
# Windows: 會解析為 C:\Users\USER\AppData\Local\Temp\...
LOG_FILENAME = os.path.join(tempfile.gettempdir(), 'reliability_errors.log')

# 設置日誌的格式和級別
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8',  # 確保 Windows/PyCharm 環境下中文字符正確輸出
    handlers=[
        logging.StreamHandler(sys.stdout),  # 輸出到 Console/終端機
        logging.FileHandler(LOG_FILENAME, mode='a', encoding='utf-8')  # 輸出到檔案 (append mode)
    ]
)
logger = logging.getLogger(__name__)


# 註冊清理函數：確保程式退出時，日誌檔案句柄被正確關閉，防止數據丟失。
def cleanup_logging():
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)
    logger.info("【日誌系統清理完成】已關閉檔案句柄。")


atexit.register(cleanup_logging)

# --- II. 核心測試配置 ---

TARGET_API = "https://www.google.com/robots.txt"  # 測試目標 API (可替換為您的 BMC API)
CONCURRENCY_LEVEL = 50  # 併發請求數 (模擬 50 個用戶同時訪問)
PERFORMANCE_THRESHOLD_MS = 2000  # 效能閾值：平均延遲需低於 2000 毫秒 (2 秒)


# --- III. 併發測試函數 ---

def make_request(api_url):
    """
    發送單個 HTTP GET 請求並記錄延遲時間和狀態。

    Args:
        api_url (str): 目標 API 網址。

    Returns:
        tuple: (是否成功, 請求耗時(ms), 狀態碼)
    """
    start_time = time.perf_counter()
    try:
        # timeout 設置為 5 秒，防止無限等待
        response = requests.get(api_url, timeout=5)
        # 檢查 HTTP 狀態碼 (200-299 視為成功)
        is_success = 200 <= response.status_code < 300
        status_code = response.status_code
    except requests.exceptions.RequestException as e:
        # 捕獲所有請求相關錯誤 (例如超時、連接錯誤)
        logger.error(f"請求失敗: {api_url} 發生錯誤: {e}", exc_info=False)
        is_success = False
        status_code = -1  # 用 -1 表示連接/超時錯誤

    end_time = time.perf_counter()
    latency_ms = (end_time - start_time) * 1000  # 轉換為毫秒

    return (is_success, latency_ms, status_code)


def run_concurrent_test(api_url, concurrency):
    """
    使用線程池執行併發測試。

    Args:
        api_url (str): 目標 API。
        concurrency (int): 併發數量。

    Returns:
        tuple: (總失敗數, 延遲時間列表(ms))
    """
    logger.info(f"--- 開始 {concurrency} 併發可靠度測試 (目標: {api_url}) ---")

    total_failures = 0
    all_latencies = []

    # 使用 ThreadPoolExecutor 進行多線程併發
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        # 提交所有請求任務
        futures = [executor.submit(make_request, api_url) for _ in range(concurrency)]

        # 收集結果
        for future in concurrent.futures.as_completed(futures):
            is_success, latency, status_code = future.result()
            all_latencies.append(latency)

            if not is_success:
                total_failures += 1
                if status_code != -1:  # -1 是連接錯誤，其他是 HTTP 錯誤碼
                    logger.error(f"請求失敗 (HTTP 狀態碼: {status_code})")

    logger.info("--- 併發測試完成 ---")
    return total_failures, all_latencies


# --- IV. Pytest 測試類別 ---

class TestApiReliability:
    """
    包含 VQE (供應商質量工程) 框架的兩個核心測試。
    """

    def setup_class(self):
        """
        在類別中的所有測試方法運行前執行一次 (初始化)。
        執行併發測試，並將結果存儲在類別變數中供後續測試使用。
        """
        self.total_failures, self.all_latencies = run_concurrent_test(
            TARGET_API, CONCURRENCY_LEVEL
        )
        self.total_requests = CONCURRENCY_LEVEL

        # 額外資訊輸出，幫助追蹤日誌位置
        logger.info(f"【日誌追溯路徑】詳細報告已寫入檔案: {LOG_FILENAME}")

    def test_reliability_zero_error_rate(self):
        """
        測試 I：可靠度驗證 (Reliability Test)。
        要求：錯誤率必須為 0%。
        """
        error_rate = (self.total_failures / self.total_requests) * 100
        logger.info(f"總請求數: {self.total_requests}, 失敗數: {self.total_failures}")

        assert self.total_failures == 0, f"可靠度測試失敗：錯誤請求數為 {self.total_failures} ({error_rate:.2f}%)"
        logger.info(f"✅ 可靠度測試通過：錯誤率為 {error_rate:.2f}%。")

    def test_performance_statistics_analysis(self):
        """
        測試 II：效能驗證 (Performance Test)。
        計算並分析平均延遲、P95 延遲和穩定性指標 (標準差)。
        """
        latencies = self.all_latencies

        # 1. 計算統計數據
        avg_latency = statistics.mean(latencies)
        std_dev = statistics.stdev(latencies) if len(latencies) > 1 else 0

        # 2. 計算 P95 延遲 (將延遲時間排序，取第 95 百分位數)
        sorted_latencies = sorted(latencies)
        # P95 的索引位置 (例如 50 個請求中，索引為 47)
        p95_index = int(len(sorted_latencies) * 0.95) - 1
        p95_latency = sorted_latencies[p95_index]

        # 3. 輸出報告
        logger.info("--- 效能統計數據報告 ---")
        logger.info(f"目標 API: {TARGET_API}")
        logger.info(f"併發請求數: {CONCURRENCY_LEVEL}")
        logger.info(f"平均延遲 (Avg Latency): {avg_latency:.2f} ms")
        logger.info(f"標準差 (Std Dev): {std_dev:.2f} ms (VQE 穩定性指標)")
        logger.info(f"P95 延遲: {p95_latency:.2f} ms")
        logger.info(f"效能閾值 (Threshold): {PERFORMANCE_THRESHOLD_MS} ms")
        logger.info("---------------------------")

        # 4. 進行效能斷言 (Assertion)
        assert avg_latency < PERFORMANCE_THRESHOLD_MS, \
            f"效能測試失敗：平均延遲 {avg_latency:.2f} ms 超過閾值 {PERFORMANCE_THRESHOLD_MS} ms。"

        logger.info(f"✅ 效能測試通過：平均延遲低於 {PERFORMANCE_THRESHOLD_MS} ms。")
