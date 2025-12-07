import base64
import re
import requests
from typing import Optional
from bs4 import BeautifulSoup

from lib.ocr.base_ocr import BaseOCR
from schemas.schema import OCRLLMPayload


class ChandraOCR(BaseOCR):
    """使用 ChandraOCR 服務進行批次和單張圖片 OCR 處理的類別"""

    def __init__(
        self,
        llm_payload: OCRLLMPayload,
        output_dir: Optional[str] = None,
        mode: str = "vllm",
        local_service_url: str = "http://localhost:8080/ocr"
    ):
        """
        初始化 ChandraOCR 客戶端

        Args:
            llm_payload: LLM API payload 配置物件
            output_dir: 保存 OCR 結果的目錄（預設：與輸入目錄相同）
            mode: OCR 模式，'local' 或 'vllm'（預設：'vllm'）
            local_service_url: 本地 ChandraOCR 服務的 URL
        """
        super().__init__(llm_payload, output_dir, mode)
        self.local_service_url = local_service_url

    def call_local(self, image_url: str) -> str:
        """
        呼叫本地 OCR 服務對單張圖片執行 OCR

        Args:
            image_url: 圖片的 URL 或 base64 data URL

        Returns:
            生成的 OCR 文字

        # 將圖片編碼為 base64 data URL（如果還不是的話）
        encoded_image = self._encode_image(image_url)

        # 從 data URL 中提取 base64 數據
        img_data = encoded_image
        if "," in img_data:
            img_bytes = base64.b64decode(img_data.split(",")[1])
        else:
            # 如果沒有 data URL 前綴，直接解碼
            img_bytes = base64.b64decode(img_data)

        # 準備文件上傳
        files = {"file": ("image.jpg", img_bytes, "image/jpeg")}

        try:
            # 發送 POST 請求到本地服務
            response = requests.post(
                "http://192.168.1.79:3677/predict",
                files=files,
                timeout=300
            )
            response.raise_for_status()

            # 返回 OCR 結果
            result = response.json()
            return result.get('text', result.get('result', str(result)))

        except requests.exceptions.RequestException as e:
            error_msg = f"本地 OCR 服務請求失敗：{e}"
            print(error_msg)
            raise
        """
        raise NotImplementedError("Local mode is not implemented for ChandraOCR.")

    def OutputParser(self, html_content: str) -> str:
        """
        從 HTML 內容中提取純文字

        Args:
            html_content: 包含 HTML 標籤的內容

        Returns:
            提取的純文字，標籤內容以換行符分隔
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        text = soup.get_text(separator="\n", strip=True)
        return text

    def call_vllm_method(self, image_url: str, task: str = "ocr") -> str:
        encoded_image = self._encode_image(image_url)

        # 構建請求數據
        prompt = "Extract text from this image"

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
                    {"type": "text", "text": prompt}
                ]
            }
        ]

        # 使用 llm_payload 構建完整的 payload，並覆蓋特定參數
        payload = self.llm_payload.build_chat_payload(
            messages,
            additional_params={"temperature": 0.0, "top_p": 0.1}
        )

        # 請求頭
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer EMPTY"
        }

        try:
            response = requests.post(
                self.llm_payload.base_url,
                json=payload,
                headers=headers,
                timeout=self.llm_payload.timeout
            )
            response.raise_for_status()

            result = response.json()
            return self.OutputParser(result['choices'][0]['message']['content'])
        except requests.exceptions.HTTPError as e:
            print(f"HTTP 錯誤：{e}")
            print(f"請求 URL：{self.llm_payload.base_url}")
            print(f"回應內容：{response.text}")
            raise

