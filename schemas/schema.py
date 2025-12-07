"""輸入/輸出資料結構定義

本模組定義了 PDF 轉圖片和 OCR 處理的資料結構（schemas）。
"""

from typing import List, Optional, Literal, Any, Dict
from dataclasses import dataclass, asdict
from pydantic import BaseModel, Field
from pathlib import Path


# ============================================================================
# PDF 轉圖片資料結構
# ============================================================================

@dataclass
class PDFToImageInput:
    """PDF 轉圖片的輸入資料結構

    屬性:
        pdf_path: PDF 檔案路徑
        output_dir: 圖片輸出目錄
        dpi: 圖片解析度（預設：200）
        fmt: 圖片格式（預設：PNG）
        filename_prefix: 輸出檔名前綴（預設：使用 PDF 檔名）
    """
    pdf_path: str
    output_dir: str
    dpi: int = 200
    fmt: str = "PNG"
    filename_prefix: Optional[str] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class PDFToImageOutput:
    """單一 PDF 轉圖片的輸出資料結構

    屬性:
        pdf_path: 原始 PDF 檔案路徑
        output_dir: 圖片儲存目錄
        image_paths: 生成的圖片檔案路徑列表
        total_pages: 轉換的總頁數
        raw_pdf_text: PDF 原始文字內容
        status: 轉換狀態（'success' 或 'failed'）
        error: 失敗時的錯誤訊息
    """
    pdf_path: str
    output_dir: str
    image_paths: List[str]
    total_pages: int
    raw_pdf_text: List[str]
    status: Literal['success', 'failed'] = 'success'
    error: Optional[str] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class PDFBatchInput:
    """批次 PDF 轉圖片的輸入資料結構

    屬性:
        input_dir: 包含 PDF 檔案的輸入目錄
        output_dir: 圖片輸出目錄
        recursive: 是否遞迴搜尋子目錄（預設：False）
        dpi: 圖片解析度（預設：200）
        fmt: 圖片格式（預設：PNG）
        filename_prefix: 輸出檔名前綴
    """
    input_dir: str
    output_dir: str
    recursive: bool = False
    dpi: int = 200
    fmt: str = "PNG"
    filename_prefix: Optional[str] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class PDFBatchOutput:
    """批次 PDF 轉圖片的輸出資料結構

    屬性:
        total: 處理的 PDF 總數
        success: 成功轉換的數量
        failed: 失敗的數量
        results: 各個 PDF 的轉換結果列表
    """
    total: int
    success: int
    failed: int
    results: List[PDFToImageOutput]

    def to_dict(self):
        return asdict(self)


# ============================================================================
# OCR 資料結構
# ============================================================================

@dataclass
class OCRLLMPayload:
    """OCR 的 LLM API 呼叫 payload 配置類別"""

    base_url: str = "http://localhost:8000/v1"
    model: str = "default-model"
    temperature: float = 0.0
    max_tokens: int = 18000
    top_p: float = 0.9
    frequency_penalty: float = 0.1
    presence_penalty: float = 0.1
    timeout: int = 3600

    def to_dict(self) -> Dict[str, Any]:
        """
        將 payload 轉換為字典格式

        Returns:
            包含所有配置的字典
        """
        return asdict(self)

    def get_api_params(self) -> Dict[str, Any]:
        """
        獲取 API 請求所需的參數（排除 base_url 和 timeout）

        Returns:
            API 請求參數字典
        """
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty
        }

    def build_chat_payload(
        self,
        messages: list,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        構建聊天 API 的完整 payload

        Args:
            messages: 聊天訊息列表
            additional_params: 額外的參數（會覆蓋預設值）

        Returns:
            完整的 API payload
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty
        }

        # 合併額外參數
        if additional_params:
            payload.update(additional_params)

        return payload

    def update(self, **kwargs) -> None:
        """
        更新配置參數

        Args:
            **kwargs: 要更新的參數
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise ValueError(f"未知的參數: {key}")


@dataclass
class OCROutput:
    """單一圖片 OCR 處理的輸出資料結構

    屬性:
        image_url: 原始圖片 URL 或檔案路徑
        task: 執行的 OCR 任務類型
        ocr_result: OCR 辨識結果文字
        status: 處理狀態（'success' 或 'failed'）
        error: 失敗時的錯誤訊息
    """
    image_url: str
    task: str
    ocr_result: str
    status: Literal['success', 'failed'] = 'success'
    error: Optional[str] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class OCRBatchOutput:
    """批次 OCR 處理的輸出資料結構

    屬性:
        task: 執行的 OCR 任務類型
        total_images: 處理的圖片總數
        success: 成功處理的數量
        failed: 失敗的數量
        results: 各個圖片的 OCR 結果列表
        output_file: 批次結果 JSON 檔案的儲存路徑
    """
    task: str
    total_images: int
    success: int
    failed: int
    results: List[OCROutput]
    output_file: Optional[str] = None

    def to_dict(self):
        return asdict(self)
    

# ============================================================================
# LLMAugmenter 資料結構
# ============================================================================

@dataclass
class VLLMPayload:
    vllm_url: str
    model_name: str
    max_tokens: int = 18000
    temperature: float = 0.7
    top_p: float = 0.9
    frequency_penalty: float = 0.1
    presence_penalty: float = 0.1
    is_thinking_mode: bool = False
    limit_llmoutput_scheme: bool = False

@dataclass
class OpenRouterPayload:
    api_key: str
    url: str
    model_name: str
    max_tokens: int = 18000
    temperature: float = 0.7
    top_p: float = 0.9
    frequency_penalty: float = 0.1
    presence_penalty: float = 0.1
    is_thinking_mode: bool = False


class LLMAugmenterInput(BaseModel):
    """原始回答資料（Pipeline 輸入）"""
    source: Dict[str, Any] = Field(..., description="問題增生關鍵字")

    class Config:
        json_schema_extra = {
            "example": {
                "source": {
                    "title": "表12-4中醫門診總額一般服務項目執行情形\n",
                    "製表人": "製表人：陳聿萱，分機：2626",
                    "備註": "註：1.各年度預算數：112年編列預算如下，合計714.6百萬元，後續年度預數算為前一年預算\n        ×(1+當年一般服務成長率)。\n     (1)協商因素之「多重慢性疾病之中醫醫療照護密集度」經費為476.7百萬元。\n     (2)非協商因素之「醫療服務成本指數改變率」經費為237.9百萬元。\n    2.112年新增「多重慢性疾病之中醫醫療照護密集度」，預算476.7百萬元，新增支付標準A91\n      整合醫療照護費加計(70點/件)，自112.3.1生效，支付標準規定：\n     (1)收案對象：慢性病或重大傷病，且為多重疾病。\n     (2)診療時間合計10分鐘以上，並根據診斷結果至少提供1項中醫醫療衛教(如中醫飲食衛教、\n         穴位經絡衛教、簡易中醫運動衛教或各類中藥使用衛教等)，並於病歷記錄評估結果及\n        所提供之中醫醫療衛教項目。\n    3.執行目標及預期效益評估指標如上表，以112年修訂支付標準後之實施時程等比率換算目\n       標值，112年執行目標人次為567.5萬人次(681萬人次×10/12)。\n    4.114年預算執行率，以申報點數為分子，並擷取到總額協商前可取得之月份(如1~6月或1~5月)。",
                },
            }
        }

class LLMAugmenterOutput(BaseModel):
    """原始回答資料（Pipeline 輸入）"""
    augmented_queries: List[str]
    raw_response: Dict

    class Config:
        json_schema_extra = {
            "example": {
                "augmented_queries": [
                    "民國112年執行目標人次數",
                    "2023年度目標執行數",
                    "112年服務人次目標值"
                ],
            }
        }

class LLMParserSchema(BaseModel):
    """LLM 輸出格式限制 Schema（用於 guided_json）"""
    queries: List[str] = Field(
        ...,
        description="生成的查詢變體列表，應包含3-5個不同表達方式的問題",
        min_items=3,
        max_items=5
    )

    class Config:
        json_schema_extra = {
            "example": {
                "queries": [
                    "民國112年執行目標人次數",
                    "2023年度目標執行數",
                    "112年服務人次目標值"
                ]
            }
        }

# ============================================================================
# 最終結果資料結構
# ============================================================================

@dataclass
class AutoGenOutput:
    """LLM 原始輸出資料（用於儲存完整的 API 回應）"""
    source_path: str
    ocr_text: str
    questions: List[str]

    def to_dict(self):
        return asdict(self)

@dataclass
class AutoGenRawOutput:
    """LLM 原始輸出資料（用於儲存完整的 API 回應）"""
    source_path: str
    mode: str
    model_name: str
    ocr_text: str
    raw_response: Dict

    def to_dict(self):
        return asdict(self)

# ============================================================================
# 流程管線資料結構 (PDF -> 圖片 -> OCR)
# ============================================================================

@dataclass
class PDFOCRPipelineInput:
    """完整 PDF 到 OCR 流程管線的輸入資料結構

    屬性:
        pdf_path: 輸入 PDF 檔案路徑
        output_dir: 所有輸出的基礎目錄
        pdf_dpi: PDF 轉圖片的解析度（預設：200）
        pdf_format: PDF 轉換的圖片格式（預設：PNG）
        ocr_task: OCR 任務類型（預設：ocr）
        ocr_base_url: VLLM 伺服器 URL
        ocr_model: OCR 模型名稱
        ocr_timeout: OCR 請求超時時間（預設：3600）
        ocr_temperature: OCR 採樣溫度（預設：0.0）
    """
    pdf_path: str
    output_dir: str
    pdf_dpi: int = 200
    pdf_format: str = "PNG"
    ocr_task: Literal['ocr', 'table', 'formula', 'chart'] = 'ocr'
    ocr_base_url: str = "http://localhost:8000/v1"
    ocr_model: str = "PaddlePaddle/PaddleOCR-VL"
    ocr_timeout: int = 3600
    ocr_temperature: float = 0.0

    def to_dict(self):
        return asdict(self)


@dataclass
class PDFOCRPipelineOutput:
    """完整 PDF 到 OCR 流程管線的輸出資料結構

    屬性:
        pdf_path: 原始 PDF 檔案路徑
        pdf_conversion: PDF 轉圖片的轉換結果
        ocr_results: OCR 處理結果
        total_pages: 處理的總頁數
        output_dir: 基礎輸出目錄
        status: 整體流程狀態（'success', 'partial', 'failed'）
        errors: 處理過程中遇到的錯誤列表
    """
    pdf_path: str
    pdf_conversion: dict
    ocr_results: dict
    total_pages: int
    output_dir: str
    status: Literal['success', 'partial', 'failed'] = 'success'
    errors: List[str] = None

    def to_dict(self):
        result = asdict(self)
        if result['errors'] is None:
            result['errors'] = []
        return result

# ============================================================================
# 使用範例
# ============================================================================

if __name__ == "__main__":
    # 範例：PDF 轉圖片輸入
    pdf_input = PDFToImageInput(
        pdf_path="/path/to/document.pdf",
        output_dir="/path/to/output",
        dpi=300,
        fmt="PNG"
    )
    print("PDF 轉圖片輸入資料結構:")
    print(pdf_input.to_dict())
    print()

    # 範例：流程管線輸入
    pipeline_input = PDFOCRPipelineInput(
        pdf_path="/path/to/document.pdf",
        output_dir="/path/to/output",
        pdf_dpi=200,
        ocr_task="table",
        ocr_base_url="http://192.168.1.79:8074/v1"
    )
    print("PDF-OCR 流程管線輸入資料結構:")
    print(pipeline_input.to_dict())
