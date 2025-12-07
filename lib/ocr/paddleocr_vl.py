import base64
import requests
from typing import Optional

from lib.ocr.base_ocr import BaseOCR
from schemas.schema import OCRLLMPayload


class PaddleOCR(BaseOCR):
    """使用 VLLM 進行批次和單張圖片 OCR 處理的 PaddleOCR 類別"""

    # 任務特定的基礎提示詞
    TASKS = {
        "ocr": "OCR:",
        "table": "Table Recognition:",
        "formula": "Formula Recognition:",
        "chart": "Chart Recognition:",
    }

    def __init__(
        self,
        llm_payload: OCRLLMPayload,
        output_dir: Optional[str] = None,
        mode: str = "local"
    ):
        """
        初始化 PaddleOCR 客戶端

        Args:
            llm_payload: LLM API payload 配置物件
            output_dir: 保存 OCR 結果的目錄（預設：與輸入目錄相同）
            mode: OCR 模式，'local' 或 'vllm'（預設：'local'）
        """
        super().__init__(llm_payload, output_dir, mode)


    def call_local(self, image_url: str) -> str:
        """
        呼叫本地 OCR 服務對單張圖片執行 OCR

        Args:
            image_url: 圖片的 URL 或 base64 data URL

        Returns:
            生成的 OCR 文字
        """
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
                self.base_url,
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

    def call_vllm_method(self, image_url: str, task: str = "ocr") -> str:
        """
        呼叫 VLLM 方法對單張圖片執行 OCR

        Args:
            image_url: 圖片的 URL 或路徑
            task: 任務類型（ocr, table, formula, chart）

        Returns:
            生成的 OCR 文字
        """
        if task not in self.TASKS:
            raise ValueError(f"無效的任務：{task}。必須是 {list(self.TASKS.keys())} 其中之一")

        # 將圖片路徑轉換為 base64 data URL
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
                        "text": self.TASKS[task]
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