import os
import json
import base64
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from abc import ABC, abstractmethod

from schemas.schema import (
    OCROutput,
    OCRBatchOutput,
    OCRLLMPayload,
)


class BaseOCR(ABC):
    """OCR 處理的通用基礎類別"""

    def __init__(
        self,
        llm_payload: OCRLLMPayload,
        output_dir: Optional[str] = None,
        mode: str = "local"
    ):
        """
        初始化 OCR 客戶端

        Args:
            llm_payload: LLM API payload 配置物件
            output_dir: 保存 OCR 結果的目錄（預設：與輸入目錄相同）
            mode: OCR 模式，'local'、'vllm' 或 'openrouter'（預設：'local'）
        """
        # 從 llm_payload 載入配置
        self.llm_payload = llm_payload
        self.base_url = llm_payload.base_url
        self.model = llm_payload.model
        self.timeout = llm_payload.timeout
        self.temperature = llm_payload.temperature
        self.max_tokens = llm_payload.max_tokens
        self.frequency_penalty = llm_payload.frequency_penalty
        self.presence_penalty = llm_payload.presence_penalty
        self.top_p = llm_payload.top_p

        self.output_dir = output_dir
        self.mode = mode

        # 驗證模式
        if self.mode not in ["local", "vllm", "openrouter"]:
            raise ValueError(f"無效的模式：{self.mode}。必須是 'local'、'vllm' 或 'openrouter'。")


    def _encode_image(self, image_path: str) -> str:
        """
        將圖片編碼為 base64 data URL

        Args:
            image_path: 圖片檔案路徑

        Returns:
            base64 編碼的 data URL
        """
        # 如果已經是 URL（http/https/data/file），直接返回
        if image_path.startswith(('http://', 'https://', 'data:', 'file://')):
            return image_path

        # 讀取圖片並轉為 base64
        with open(image_path, 'rb') as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')

        # 根據檔案副檔名決定 MIME 類型
        ext = Path(image_path).suffix.lower()
        mime_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.webp': 'image/webp'
        }
        mime_type = mime_types.get(ext, 'image/png')

        return f"data:{mime_type};base64,{image_data}"

    @abstractmethod
    def call_local(self, image_url: str) -> str:
        """
        呼叫本地 OCR 服務對單張圖片執行 OCR（需由子類實作）

        Args:
            image_url: 圖片的 URL 或 base64 data URL

        Returns:
            生成的 OCR 文字
        """
        pass

    @abstractmethod
    def call_vllm_method(self, image_url: str, task: str = "ocr") -> str:
        """
        呼叫 VLLM 方法對單張圖片執行 OCR（需由子類實作）

        Args:
            image_url: 圖片的 URL 或路徑
            task: 任務類型（ocr, table, formula, chart）

        Returns:
            生成的 OCR 文字
        """
        pass

    def single_ocr(self, image_url: str, task: str = "ocr") -> OCROutput:
        """
        對單張圖片執行 OCR 並建立輸出結構

        Args:
            image_url: 圖片的 URL 或路徑
            task: 任務類型（ocr, table, formula, chart）

        Returns:
            OCROutput 物件，包含圖片路徑和 OCR 結果
        """
        print(f"正在處理圖片：{image_url}")

        try:
            # 根據模式選擇呼叫方法
            if self.mode == "local":
                ocr_result = self.call_local(image_url)
            elif self.mode == "vllm":
                ocr_result = self.call_vllm_method(image_url, task)
            elif self.mode == "openrouter":
                ocr_result = self.call_openrouter(image_url)
            else:
                raise ValueError(f"無效的模式：{self.mode}")

            print(f"生成的文字：{ocr_result[:100]}..." if len(ocr_result) > 100 else f"生成的文字：{ocr_result}")

            # 建立輸出結構
            return OCROutput(
                image_url=image_url,
                task=task,
                ocr_result=ocr_result,
                status='success',
                error=None
            )

        except Exception as e:
            error_msg = f"OCR 處理失敗：{e}"
            print(error_msg)
            return OCROutput(
                image_url=image_url,
                task=task,
                ocr_result="",
                status='failed',
                error=error_msg
            )

    def batch_ocr(self, in_dir: str, task: str = "ocr", recursive: bool = True) -> OCRBatchOutput:
        """
        對目錄中的所有 PNG 圖片執行 OCR，並將所有結果儲存成單一 JSON 檔案

        Args:
            in_dir: 包含 PNG 圖片的輸入目錄
            task: 任務類型（ocr, table, formula, chart）
            recursive: 是否遞迴搜尋子目錄（預設：True）

        Returns:
            OCRBatchOutput 物件，包含所有處理結果
        """
        in_path = Path(in_dir)

        if not in_path.exists():
            raise ValueError(f"輸入目錄不存在：{in_dir}")

        if not in_path.is_dir():
            raise ValueError(f"輸入路徑不是目錄：{in_dir}")

        # 遞迴或非遞迴搜尋所有 PNG 檔案
        if recursive:
            png_files = sorted(in_path.rglob("*.png"))
        else:
            png_files = sorted(in_path.glob("*.png"))

        if not png_files:
            print(f"在 {in_dir} 中找不到 PNG 檔案")
            return OCRBatchOutput(
                task=task,
                total_images=0,
                success=0,
                failed=0,
                results=[],
                output_file=None
            )

        print(f"找到 {len(png_files)} 個 PNG 檔案待處理")

        results = []
        success_count = 0
        failed_count = 0

        for i, png_file in enumerate(png_files, 1):
            print(f"\n[{i}/{len(png_files)}] 處理：{png_file}")
            ocr_result = self.single_ocr(str(png_file), task)

            # 直接儲存 OCROutput 物件
            results.append(ocr_result)

            if ocr_result.status == 'success':
                success_count += 1
            else:
                failed_count += 1

        print(f"\n成功處理 {success_count}/{len(png_files)} 張圖片")

        # 批次儲存所有結果到單一 JSON 檔案
        output_file = None
        if results:
            output_file = self._save_batch_results(results, task)

        # 建立並回傳 OCRBatchOutput
        return OCRBatchOutput(
            task=task,
            total_images=len(png_files),
            success=success_count,
            failed=failed_count,
            results=results,
            output_file=output_file
        )

    def _getuuid(self, image_url: str) -> str:
        """
        從圖片路徑提取 UUID

        Args:
            image_url: 圖片路徑，例如 "results/pdf2png/moea/1111207162322696_1/1111207162322696_1_page_0001.png"

        Returns:
            UUID，包含署名 (e.g., moea)，文件 id 及頁碼，
            例如 "moea/1111207162322696_1/1111207162322696_1_page_0001"
        """
        # 移除檔案副檔名
        path_without_ext = os.path.splitext(image_url)[0]

        # 分割路徑
        parts = path_without_ext.split('/')

        # 找到 "pdf2png" 之後的所有部分
        if 'pdf2png' in parts:
            pdf2png_index = parts.index('pdf2png')
            # 取得 pdf2png 之後的所有部分並用 / 連接
            uuid = '/'.join(parts[pdf2png_index + 1:])
            return uuid

        # 如果沒有找到 "pdf2png"，返回檔名（不含副檔名）
        return parts[-1]

    def _save_batch_results(self, results: List[OCROutput], task: str) -> str:
        """
        將批次處理的所有結果儲存到單一 JSON 檔案

        Args:
            results: 所有處理結果的列表（OCROutput 物件）
            task: 任務類型（ocr, table, formula, chart）

        Returns:
            儲存的 JSON 檔案路徑
        """
        # 生成時間戳記（格式：YYYYMMDD_HHMMSS）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 決定輸出目錄
        if self.output_dir:
            output_path = Path(self.output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
        else:
            output_path = Path.cwd()

        # 建立輸出檔名（加入時間戳記）
        output_file = output_path / f"batch_ocr.json"

        # 將 OCROutput 物件轉換為字典
        results_dict = [result.to_dict() for result in results]

        # 建立批次結果結構
        batch_output = {
            "task": task,
            "total_images": len(results),
            "results": results_dict
        }

        # 保存到 JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(batch_output, f, indent=2, ensure_ascii=False)

        print(f"\n已保存批次結果到：{output_file}")
        return str(output_file)

    def _save_result(self, image_url: str, output_schema: Dict[str, str]) -> None:
        """
        保存單張圖片的 OCR 結果到 JSON 檔案（已棄用，改用 _save_batch_results）

        Args:
            image_url: 原始圖片 URL/路徑
            output_schema: 輸出結構字典
        """
        # 生成時間戳記（格式：YYYYMMDD_HHMMSS）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 決定輸出目錄
        if self.output_dir:
            output_path = Path(self.output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
        else:
            # 使用與輸入圖片相同的目錄
            image_path = Path(image_url)
            output_path = image_path.parent

        # 建立輸出檔名（將 .png 替換為 .json）
        output_file = output_path / f"ocr.json"

        # 保存到 JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_schema, f, indent=2, ensure_ascii=False)

        print(f"已保存結果到：{output_file}")
