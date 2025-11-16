#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Open WebUI Pipeline - Excel 資料增強服務
"""

from typing import List, Union, Generator, Iterator
from pydantic import BaseModel
import requests
import base64
import os
from pathlib import Path


class Pipeline:
    """Open WebUI Pipeline for Excel Data Augmentation Service"""

    class Valves(BaseModel):
        """Pipeline 配置參數"""
        API_BASE_URL: str = "http://localhost:8000"
        UPLOAD_DIR: str = "/workspace/root/venv_manager/llm_auagmenter/lib/python3.12/site-packages/open_webui/data/uploads"

        PARSER_URL: str = "https://openrouter.ai/api"
        PARSER_MODEL: str = "openai/gpt-oss-20b:free"
        PARSER_API_KEY: str = "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"
        PARSER_USE_OPENROUTER: bool = True
        PARSER_MAX_RETRIES: int = 3

        AUGMENTER_URL: str = "https://openrouter.ai/api"
        AUGMENTER_MODEL: str = "openai/gpt-oss-20b:free"
        AUGMENTER_API_KEY: str = "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"
        AUGMENTER_USE_OPENROUTER: bool = True
        AUGMENTER_MAX_RETRIES: int = 3
        AUGMENTER_PROMPT_NAME: str = "default"

        SKIP_PARSER: bool = False

    def __init__(self):
        self.type = "manifold"
        self.valves = self.Valves()
        self.pipelines = [{"id": "excel_augment", "name": "Excel Data Augmenter"}]

    def pipes(self) -> List[dict]:
        return self.pipelines

    def pipe(self, user_message: str, model_id: str, messages: List[dict], body: dict) -> Union[str, Generator, Iterator, dict]:
        """處理請求，從目錄讀取最新 Excel 檔案並呼叫 API"""

        # 從目錄獲取最新 Excel 檔案
        upload_dir = Path(self.valves.UPLOAD_DIR)
        if not upload_dir.exists():
            return f"目錄不存在: {self.valves.UPLOAD_DIR}"

        excel_files = list(upload_dir.glob('*.xlsx')) + list(upload_dir.glob('*.xls'))
        if not excel_files:
            return f"在 {self.valves.UPLOAD_DIR} 中未找到 Excel 檔案"

        latest_file = max(excel_files, key=lambda p: p.stat().st_mtime)

        # 呼叫 API
        try:
            with open(latest_file, 'rb') as f:
                response = requests.post(
                    f"{self.valves.API_BASE_URL}/api/v1/data_augment",
                    data={
                        "parser_url": self.valves.PARSER_URL,
                        "parser_model": self.valves.PARSER_MODEL,
                        "parser_api_key": self.valves.PARSER_API_KEY,
                        "parser_use_openrouter": str(self.valves.PARSER_USE_OPENROUTER).lower(),
                        "parser_max_retries": str(self.valves.PARSER_MAX_RETRIES),
                        "augmenter_url": self.valves.AUGMENTER_URL,
                        "augmenter_model": self.valves.AUGMENTER_MODEL,
                        "augmenter_api_key": self.valves.AUGMENTER_API_KEY,
                        "augmenter_use_openrouter": str(self.valves.AUGMENTER_USE_OPENROUTER).lower(),
                        "augmenter_max_retries": str(self.valves.AUGMENTER_MAX_RETRIES),
                        "augmenter_prompt_name": self.valves.AUGMENTER_PROMPT_NAME,
                        "skip_parser": str(self.valves.SKIP_PARSER).lower(),
                    },
                    files={'file': (latest_file.name, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')},
                    timeout=300
                )

            response.raise_for_status()
            result = response.json()

            if result.get("success"):
                # 獲取 JSON 檔案路徑並讀取
                json_path = result.get('augmented_queries_path', '')
                if json_path and os.path.exists(json_path):
                    with open(json_path, 'r', encoding='utf-8') as f:
                        json_content = f.read()
                        json_base64 = base64.b64encode(json_content.encode('utf-8')).decode('utf-8')
                        json_filename = os.path.basename(json_path)

                        return f"""### 處理完成 ✅
檔案: {latest_file.name}
記錄數: {result.get('total_count', 0)}

📄 [{json_filename}](data:application/json;base64,{json_base64})"""
                else:
                    return f"""### 處理完成 ✅
檔案: {latest_file.name}
記錄數: {result.get('total_count', 0)}
(未找到 JSON 檔案)"""
            else:
                return f"處理失敗: {result.get('error', '未知錯誤')}"

        except Exception as e:
            return f"錯誤: {str(e)}"
