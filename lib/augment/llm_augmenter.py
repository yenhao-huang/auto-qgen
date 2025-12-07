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

from schemas.schema import (
    VLLMPayload, 
    OpenRouterPayload, 
    LLMAugmenterInput, 
    LLMParserSchema, 
    LLMAugmenterOutput
)

from lib.prompt.prompt_manager import PromptManager

class LLMAugmenter:
    """使用 LLM 增強查詢的模組"""

    def __init__(
        self,
        mode: str,
        payload: dict,
        prompt_name: str = "default",
        verify_connection: bool = True
    ):
        """
        初始化 LLM Augmenter

        Args:
            payload: 跟服務溝通封包
            prompt_name: Prompt 名稱（預設：default）
            mode: "openrouter"、"vllm"
            verify_connection: 初始化時是否驗證 API 連線（預設：False）
        """
        self.mode = mode
        self.payload = payload
        self.max_retries = 1
        self.session = requests.Session()
        self.prompt_manager = PromptManager(prompt_name)
        print(f"✓ 已載入 Prompt corpus：'{self.prompt_manager.prompt_template}'")

        if verify_connection:
            self.test_connection()

    def _parse_payload(self):
        if self.mode == "vllm":
            return VLLMPayload(**self.payload)
        elif self.mode == "openrouter":
            return OpenRouterPayload(**self.payload)
        else:
            raise ValueError(f"Unknown mode: {self.mode}")
            

    def test_connection(self) -> bool:
        """
        測試 API 連線是否正常

        Returns:
            bool: 連線成功返回 True，失敗則拋出異常

        Raises:
            ValueError: 不支援的模式
            ConnectionError: 連線失敗
        """
        payload = self._parse_payload()

        if self.mode == "vllm":
            success = self._test_vllm_connection(payload)
        elif self.mode == "openrouter":
            success = self._test_openrouter_connection(payload)
        else:
            raise ValueError(f"Unknown mode: {self.mode}")

        if not success:
            raise ConnectionError(f"API 連線測試失敗（mode: {self.mode}）")

        return success

    def _test_vllm_connection(self, payload: VLLMPayload) -> bool:
        print(f"正在測試 API 連線：{payload.vllm_url}")
              
        headers = {"Content-Type": "application/json"}

        test_data = {
            "model": payload.model_name,
            "messages": [{"role": "user", "content": "test"}],
            "max_tokens": 5
        }
    
        try:
            response = self.session.post(
                payload.vllm_url,
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

    def _test_openrouter_connection(self, payload: OpenRouterPayload) -> bool:
        print(f"正在測試 API 連線：{payload.url}")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {payload.api_key}"
        }

        test_data = {
            "model": payload.model_name,
            "messages": [{"role": "user", "content": "test"}],
            "max_tokens": 5
        }

        try:
            response = self.session.post(
                payload.url,
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

    def augment(self, example: LLMAugmenterInput) -> LLMAugmenterOutput:
        """
        增強單一查詢

        Args:
            example: 原始回答資料

        Returns:
            LLMAugmenterOutput: 增強後的查詢，包含 raw_response 和 augmented_queries
        """
        payload = self._parse_payload()

        # 提取資訊和生成查詢變體
        if self.mode == "vllm":
            raw_response = self._call_vllm(payload, example.source)
        elif self.mode == "openrouter":
            raw_response = self._call_openrouter(payload, example.source)

        # 解析 raw_response
        if raw_response:
            parsed_queries = self.parse_result(payload, raw_response)
        else:
            parsed_queries = []

        return LLMAugmenterOutput(
            augmented_queries=parsed_queries,
            raw_response=raw_response
        )

    def _process_source(self, source: Dict):
        text_context = "\n".join(f"{k}：{v}" for k, v in source.items() if isinstance(v, str))

        return {
            "text": text_context
        }

    def _call_openrouter(self, payload: OpenRouterPayload, source: Dict) -> Dict:
        """
        呼叫 OpenRouter API 生成問題

        Args:
            source: 生問題的來源

        Returns:
            Dict: raw JSON response from API
        """

        # 來源處理
        context = self._process_source(source)

        # 使用 PromptManager 生成 prompt
        prompt = self.prompt_manager.generate_prompt_text(context["text"])

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {payload.api_key}"
        }

        data = {
            "model": payload.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": payload.max_tokens,
            "temperature": payload.temperature,
            "top_p": payload.top_p,
            "frequency_penalty": payload.frequency_penalty,
            "presence_penalty": payload.presence_penalty,
        }

        for attempt in range(self.max_retries):
            try:
                response = self.session.post(
                    payload.url,
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
                        print(f"完整 URL：{payload.url}")
                        raise ValueError(f"API 返回 HTML 而非 JSON，請檢查 API URL 是否正確")

                    return response.json()
                else:
                    print(f"API 呼叫失敗（嘗試 {attempt + 1}/{self.max_retries}）：狀態碼 {response.status_code}")
                    print(f"回應內容（前 500 字元）：{response.text[:500]}")

            except requests.exceptions.JSONDecodeError as e:
                print(f"JSON 解析錯誤（嘗試 {attempt + 1}/{self.max_retries}）：{e}")
                print(f"回應狀態碼：{response.status_code}")
                print(f"回應 Content-Type：{response.headers.get('Content-Type', 'unknown')}")
                print(f"回應內容（前 500 字元）：{response.text[:500]}")
                print(f"完整 API URL：{payload.url}")
            except requests.exceptions.RequestException as e:
                print(f"Network error (attempt {attempt + 1}): {e}")

            if attempt < self.max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff

        return {}


    def _call_vllm(self, payload: VLLMPayload, source: Dict) -> Dict:
        """
        呼叫 VLLM API 生成問題

        Args:
            source: 生問題的來源

        Returns:
            Dict: raw JSON response from API
        """

        # 來源處理
        context = self._process_source(source)

        # 使用 PromptManager 生成 prompt
        prompt = self.prompt_manager.generate_prompt_text(context["text"])

        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "model": payload.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": payload.max_tokens,
            "temperature": payload.temperature,
            "top_p": payload.top_p,
            "frequency_penalty": payload.frequency_penalty,
            "presence_penalty": payload.presence_penalty,
        }

        if payload.limit_llmoutput_scheme:
            data["guided_json"] = LLMParserSchema.model_json_schema()

        for attempt in range(self.max_retries):
            try:
                response = self.session.post(
                    payload.vllm_url,
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
                        print(f"完整 URL：{payload.vllm_url}")
                        raise ValueError(f"API 返回 HTML 而非 JSON，請檢查 API URL 是否正確")

                    return response.json()
                else:
                    print(f"API 呼叫失敗（嘗試 {attempt + 1}/{self.max_retries}）：狀態碼 {response.status_code}")
                    print(f"回應內容（前 500 字元）：{response.text[:500]}")

            except requests.exceptions.JSONDecodeError as e:
                print(f"JSON 解析錯誤（嘗試 {attempt + 1}/{self.max_retries}）：{e}")
                print(f"回應狀態碼：{response.status_code}")
                print(f"回應 Content-Type：{response.headers.get('Content-Type', 'unknown')}")
                print(f"回應內容（前 500 字元）：{response.text[:500]}")
                print(f"完整 API URL：{payload.vllm_url}")
            except requests.exceptions.RequestException as e:
                print(f"Network error (attempt {attempt + 1}): {e}")

            if attempt < self.max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff

        return {}

    def _parse_schmea_result(self, raw_response: Dict) -> List[str]:
        """
        從 raw response 解析出 queries

        Args:
            raw_response: API 返回的 raw JSON response

        Returns:
            List[str]: 解析出的 queries
        """

        if not raw_response:
            return []

        try:
            generated_text = raw_response["choices"][0]["message"]["content"].strip()

            # 嘗試 JSON 解析
            try:
                parsed_json = json.loads(generated_text)
                validated = LLMParserSchema(**parsed_json)
                return validated.queries
            except (json.JSONDecodeError, ValueError) as e:
                print(f"JSON parsing failed: {e}")
                print(f"Raw response: {generated_text}")
                # Fallback to old parsing method
                return self._parse_queries(generated_text)

        except (KeyError, IndexError) as e:
            print(f"Error extracting content from raw_response: {e}")
            return []

    def parse_result(self, payload, raw_response: Dict) -> List[str]:

        if payload.is_thinking_mode:
            return self._parse_thinking_result(raw_response)
        else:
            return self._parse_schmea_result(raw_response)

    def _parse_thinking_result(self, raw_response: Dict) -> List[str]:
        '''
        extract <question> </question> 內容 + # Remove numbering like "1. ", "2. ", etc.
        '''
        if not raw_response:
            return []

        try:
            generated_text = raw_response["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError) as e:
            print(f"Error extracting content from raw_response: {e}")
            return []

        # 決定要搜尋的文本範圍
        target_text = generated_text
        end_marker_match = re.search(r'<\|end\|>(.*)', generated_text, re.DOTALL)
        if end_marker_match:
            target_text = end_marker_match.group(1)

        # 使用 findall 找出所有匹配的 <question> 區塊
        matches = re.findall(r'<question>(.*?)</question>', target_text, re.DOTALL)

        if not matches:
            # Fallback: 使用整個 target_text
            content = target_text
        else:
            # 取最後一個匹配項，通常這才是真正的輸出區塊
            # 因為模型在前面可能會「提到」標籤，真正的 XML block 通常在最後
            content = matches[-1]

        return self._parse_queries(content)

    def _parse_queries(self, generated_text: str) -> List[str]:
        """
        Parse generated queries from VLLM response into a list.

        Args:
            generated_text: Raw text response from VLLM

        Returns:
            List of query strings (up to 5 queries)
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
                    # 限制最多 5 個查詢
                    if len(queries) >= 5:
                        break

        return queries