import base64
import requests
from typing import Optional
import json
import time

from lib.ocr.base_ocr import BaseOCR
from schemas.schema import OCRLLMPayload


class NVNemotronOCR(BaseOCR):
    """使用 NVNemotronOCR 服務進行批次和單張圖片 OCR 處理的類別"""

    def __init__(
        self,
        llm_payload: OCRLLMPayload,
        output_dir: Optional[str] = None,
        mode: str = "openrouter",
        local_service_url: str = "http://localhost:8080/ocr"
    ):
        """
        初始化 NVNemotronOCR 客戶端

        Args:
            llm_payload: LLM API payload 配置物件
            output_dir: 保存 OCR 結果的目錄（預設：與輸入目錄相同）
            mode: OCR 模式，'local'、'vllm' 或 'openrouter'（預設：'openrouter'）
            local_service_url: 本地服務的 URL
        """
        super().__init__(llm_payload, output_dir, mode)
        self.local_service_url = local_service_url

    def call_openrouter(self, image_url: str) -> str:
        """
        呼叫 OpenRouter API 使用 NVIDIA Nemotron 模型進行 OCR

        Args:
            image_url: 圖片的 URL 或路徑

        Returns:
            OCR 識別的文字結果
        """
        encoded_image = self._encode_image(image_url)

        # 使用 LLMPayload 構建訊息
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": encoded_image}
                    },
                    {
                        "type": "text",
                        "text": "請執行 OCR，只輸出圖片中的文字內容，不要有任何額外說明或解釋。"
                    }
                ]
            }
        ]

        # 使用 llm_payload 構建 payload，但覆蓋 model 和 temperature
        payload = self.llm_payload.build_chat_payload(
            messages,
            additional_params={
                "model": "nvidia/nemotron-nano-12b-v2-vl:free",
                "temperature": 0.0
            }
        )

        # 構建 API 請求
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": "Bearer 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",
                "Content-Type": "application/json",
            },
            data=json.dumps(payload),
            timeout=self.llm_payload.timeout
        )

        # 檢查回應狀態
        response.raise_for_status()

        # 等待一段時間
        time.sleep(30)

        # 解析回應
        result = response.json()

        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"]
            return content.strip()
        else:
            raise ValueError(f"API 回應格式異常：{result}")

    def call_local(self, image_url: str) -> str:
        raise NotImplementedError("DotsOCR 本地服務尚未實作")

    def call_vllm_method(self, image_url: str, task: str = "ocr") -> str:
        raise NotImplementedError("DotsOCR 本地服務尚未實作")
