import base64
import requests
from typing import Optional

from lib.ocr.base_ocr import BaseOCR
from schemas.schema import OCRLLMPayload


class DotsOCR(BaseOCR):
    """使用 Dots OCR 服務進行批次和單張圖片 OCR 處理的類別"""

    def __init__(
        self,
        llm_payload: OCRLLMPayload,
        output_dir: Optional[str] = None,
        mode: str = "local",
        local_service_url: str = "http://localhost:8080/ocr"
    ):
        """
        初始化 DotsOCR 客戶端

        Args:
            llm_payload: LLM API payload 配置物件
            output_dir: 保存 OCR 結果的目錄（預設：與輸入目錄相同）
            mode: OCR 模式，'local' 或 'vllm'（預設：'local'）
            local_service_url: 本地 DotsOCR 服務的 URL
        """
        super().__init__(llm_payload, output_dir, mode)
        self.local_service_url = local_service_url

    def call_local(self, image_url: str) -> str:
        raise NotImplementedError("DotsOCR 本地服務尚未實作")

    def call_vllm_method(self, image_url: str, task: str = "ocr") -> str:
        """
        呼叫 VLLM 方法對單張圖片執行 OCR（DotsOCR 特定實作）

        Args:
            image_url: 圖片的 URL 或路徑
            task: 任務類型（ocr, table, formula, chart）

        Returns:
            生成的 OCR 文字
        """
        encoded_image = self._encode_image(image_url)

        # 使用 LLMPayload 構建訊息
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": encoded_image
                        }
                    },
                    {
                        "type": "text",
                        "text": f"執行 OCR 任務：{task}"
                    }
                ]
            }
        ]

        # 使用 llm_payload 構建完整的 payload
        payload = self.llm_payload.build_chat_payload(messages)

        try:
            response = requests.post(
                self.llm_payload.base_url,
                json=payload,
                timeout=self.llm_payload.timeout
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"HTTP 錯誤：{e}")
            print(f"請求 URL：{self.llm_payload.base_url}")
            print(f"回應內容：{response.text}")
            raise

        result = response.json()
        return result['choices'][0]['message']['content']
