#!/usr/bin/env python3
"""
LLM Augmenter Module
使用 LLM 來增強查詢，提取關鍵資訊並生成多樣化的查詢變體
"""
import argparse
from datetime import datetime
from pathlib import Path
import re
import json
import time
import requests
from typing import List, Dict, Any, Optional
from tqdm import tqdm
from pathlib import Path
from utils.schemas import GroundTruth, AugmenterInput, AugmentedQuery
from utils.prompt_manager import PromptManager

class LLMAugmenter:
    """使用 LLM 增強查詢的模組"""

    def __init__(
        self,
        vllm_url: str,
        model: str,
        prompt_name: str = "default",
        prompt_manager: Optional[PromptManager] = None,
        api_key: Optional[str] = None,
        use_openrouter: bool = False,
        verify_connection: bool = False
    ):
        """
        初始化 LLM Augmenter

        Args:
            vllm_url: LLM API URL
            model: 模型名稱
            prompt_name: Prompt 名稱（預設：default）
            prompt_manager: Prompt 管理器（可選，預設會創建新的）
            api_key: API 金鑰（OpenRouter 需要）
            use_openrouter: 是否使用 OpenRouter API（預設：False）
            verify_connection: 初始化時是否驗證 API 連線（預設：False）
        """
        self.vllm_url = vllm_url.rstrip('/')  # 移除結尾的斜線
        self.model = model
        self.prompt_name = prompt_name
        self.max_retries = 1
        self.session = requests.Session()
        self.prompt_manager = prompt_manager if prompt_manager else PromptManager()
        self.api_key = api_key
        self.use_openrouter = use_openrouter

        if verify_connection:
            self.test_connection()

    def test_connection(self) -> bool:
        """
        測試 API 連線是否正常

        Returns:
            bool: 連線成功返回 True，失敗返回 False
        """
        print(f"正在測試 API 連線：{self.vllm_url}/v1/chat/completions")

        headers = {"Content-Type": "application/json"}
        if self.use_openrouter and self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        test_data = {
            "model": self.model,
            "messages": [{"role": "user", "content": "test"}],
            "max_tokens": 5
        }

        try:
            response = self.session.post(
                f"{self.vllm_url}/v1/chat/completions",
                headers=headers,
                json=test_data,
                timeout=30
            )

            content_type = response.headers.get('Content-Type', '')

            if response.status_code == 200:
                if 'application/json' in content_type:
                    print("✓ API 連線測試成功")
                    return True
                else:
                    print(f"✗ API 返回非 JSON 格式（Content-Type: {content_type}）")
                    print(f"  回應內容：{response.text[:200]}")
                    return False
            else:
                print(f"✗ API 連線失敗：狀態碼 {response.status_code}")
                print(f"  回應內容：{response.text[:200]}")
                return False

        except Exception as e:
            print(f"✗ 連線錯誤：{e}")
            return False

    def augment(self, example: AugmenterInput) -> AugmentedQuery:
        """
        增強單一查詢

        Args:
            example: 原始回答資料

        Returns:
            AugmentedQuery: 增強後的查詢
        """

        # 提取資訊和生成查詢變體
        augmented_queries = self._call_llm_for_generation(example.keyword)

        return AugmentedQuery(
            augmented_queries=augmented_queries,
            ground_truth=example.ground_truth,
            metadata={
                "keyword" : example.keyword,
            }
        )

    def augment_batch(self, answers: List[AugmenterInput]) -> List[AugmentedQuery]:
        """
        批次增強多個查詢

        Args:
            answers: 原始回答資料列表

        Returns:
            List[AugmentedQuery]: 增強後的查詢列表
        """
        return [self.augment(answer) for answer in tqdm(answers, desc="Augmenting queries")]

    def save_augment_results(self, results: List[AugmentedQuery], output_path: str) -> None:
        """
        保存增強後的查詢結果到 JSON 檔案

        Args:
            results: 增強後的查詢列表
            output_path: 輸出檔案路徑
        """
        # 確保輸出目錄存在並獲取絕對路徑
        output_file = Path(output_path).resolve()
        output_file.parent.mkdir(parents=True, exist_ok=True)

        output_data = []
        for result in results:
            output_data.append({
                "augmented_queries": result.augmented_queries,
                "ground_truth": {
                    "file_name": result.ground_truth.file_name,
                    "item_id": result.ground_truth.item_id
                },
                "metadata": result.metadata
            })

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"✓ 已保存 {len(results)} 筆增強結果至 {output_file}")

    def _call_llm_for_generation(self, keyword: Dict) -> List[str]:
        """
        Generate prompt for VLLM API based on metadata.

        Args:
            keyword: Dictionary containing metadata fields

        Returns:
            List[str]: Generated query variants
        """
        # 格式化背景資訊
        context = "\n".join(f"{k}：{v}" for k, v in keyword.items())

        # 使用 PromptManager 生成 prompt
        prompt = self.prompt_manager.generate_prompt_text(
            prompt_name=self.prompt_name,
            context=context
        )

        # 根據是否使用 OpenRouter 設定不同的 headers
        headers = {
            "Content-Type": "application/json"
        }
        if self.use_openrouter and self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        data = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 1800,
            "temperature": 0.7,
            "top_p": 0.9,
            "frequency_penalty": 0.1,
            "presence_penalty": 0.1
        }

        for attempt in range(self.max_retries):
            try:
                response = self.session.post(
                    f"{self.vllm_url}/v1/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=120
                )

                if response.status_code == 200:
                    # 檢查回應的 Content-Type
                    content_type = response.headers.get('Content-Type', '')

                    if 'application/json' not in content_type:
                        print(f"警告：API 返回的不是 JSON 格式")
                        print(f"Content-Type: {content_type}")
                        print(f"回應內容（前 500 字元）：{response.text[:500]}")
                        print(f"完整 URL：{self.vllm_url}/v1/chat/completions")
                        raise ValueError(f"API 返回 HTML 而非 JSON，請檢查 API URL 是否正確")

                    result = response.json()

                    # 檢查回應格式
                    if "choices" not in result or len(result["choices"]) == 0:
                        print(f"錯誤：API 回應格式不正確")
                        print(f"回應內容：{json.dumps(result, ensure_ascii=False, indent=2)}")
                        raise ValueError("API 回應缺少 'choices' 欄位")

                    generated_text = result["choices"][0]["message"]["content"].strip()
                    return self.parse_queries(generated_text)
                else:
                    print(f"API 呼叫失敗（嘗試 {attempt + 1}/{self.max_retries}）：狀態碼 {response.status_code}")
                    print(f"回應內容（前 500 字元）：{response.text[:500]}")

            except requests.exceptions.JSONDecodeError as e:
                print(f"JSON 解析錯誤（嘗試 {attempt + 1}/{self.max_retries}）：{e}")
                print(f"回應狀態碼：{response.status_code}")
                print(f"回應 Content-Type：{response.headers.get('Content-Type', 'unknown')}")
                print(f"回應內容（前 500 字元）：{response.text[:500]}")
                print(f"完整 API URL：{self.vllm_url}/v1/chat/completions")
            except requests.exceptions.RequestException as e:
                print(f"Network error (attempt {attempt + 1}): {e}")

            if attempt < self.max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff

        return []

    def parse_queries(self, generated_text: str) -> List[str]:
        """
        Parse generated queries from VLLM response into a list.

        Args:
            generated_text: Raw text response from VLLM

        Returns:
            List of query strings
        """
        queries = []
        lines = generated_text.strip().split('\n')

        for line in lines:
            line = line.strip()
            # Remove numbering like "1. ", "2. ", etc.
            if line and len(line) > 2:
                # Remove pattern like "1. ", "2. ", etc.
                cleaned = re.sub(r'^\d+\.\s*', '', line)
                # Remove brackets if present
                cleaned = re.sub(r'^\[(.*)\]$', r'\1', cleaned)
                if cleaned:
                    queries.append(cleaned)

        return queries


def main():
    '''
    使用 vLLM（原本的方式）：
    python llm_augmenter.py -i input.json --vllm-url http://192.168.1.79:3472 --model gemma-12b-8bit
    使用 OpenRouter：
    python llm_augmenter.py -i input.json --use-openrouter --api-key   --vllm-url https://openrouter.ai
    '''
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    parser = argparse.ArgumentParser(
        description="LLM Augmenter：讀取輸入檔、透過 vLLM 產生查詢變體，並輸出結果 JSON。"
    )
    parser.add_argument(
        "-i", "--input", required=True, help="輸入檔路徑（JSON；list of objects）"
    )
    parser.add_argument(
        "-o",
        "--output",
        default=f"results/augmenter/augment_results_{timestamp}.json",
        help="輸出檔路徑（JSON，預設帶時間戳）"
    )
    parser.add_argument(
        "--mode", choices=["keyword"], default="keyword",
        help="處理模式：keyword"
    )
    parser.add_argument(
        "--vllm-url", default="http://192.168.1.79:3472",
        help="vLLM/OpenAI 相容 API URL"
    )
    parser.add_argument(
        "--model", default="gemma-12b-8bit", help="模型名稱（預設：gemma-12b-8bit）"
    )
    parser.add_argument(
        "--prompt-name", default="1", help="Prompt 名稱（預設：default）"
    )
    parser.add_argument(
        "--api-key", default=None, help="API 金鑰（OpenRouter 使用）"
    )
    parser.add_argument(
        "--use-openrouter", action="store_true", help="使用 OpenRouter API"
    )

    args = parser.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.output)
    if not in_path.exists():
        raise FileNotFoundError(f"找不到輸入檔：{in_path}")

    with open(in_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("輸入檔必須是 JSON 陣列（list of objects）。")

    # 準備 Augmenter
    augmenter_keyword = LLMAugmenter(
        vllm_url=args.vllm_url,
        model=args.model,
        prompt_name=args.prompt_name,
        api_key=args.api_key,
        use_openrouter=args.use_openrouter
    )

    results = []
    for idx, item in enumerate(tqdm(data, desc="Processing inputs")):
        # 共同欄位 ground_truth（必要）
        try:
            gt_raw = item["ground_truth"]
            ground_truth = GroundTruth(
                file_name=gt_raw["file_name"],
                item_id=gt_raw["item_id"],
            )
        except KeyError as e:
            raise KeyError(f"第 {idx} 筆資料缺少 ground_truth 欄位或其子欄位：{e}")

        if "keyword" not in item or not isinstance(item["keyword"], dict):
            raise ValueError(f"第 {idx} 筆 keyword 模式需要 'keyword'（dict）欄位")
        aug_in = AugmenterInput(
            keyword=item["keyword"],
            ground_truth=ground_truth,
        )
        results.append(augmenter_keyword.augment(aug_in))


    augmenter_keyword.save_augment_results(results, str(out_path))
    print(f"✓ 完成：共 {len(results)} 筆，已輸出至 {out_path}")


if __name__ == "__main__":
    main()