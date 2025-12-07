"""PDF 轉圖片轉換器

此模組提供將 PDF 檔案轉換為圖片的功能。
"""

import argparse
from pathlib import Path
from typing import List, Optional
import sys
import json

try:
    import fitz  # PyMuPDF
    from PIL import Image
except ImportError as e:
    print(f"錯誤：找不到必要的套件。請安裝：pip install PyMuPDF pillow")
    print(f"詳細資訊：{e}")
    sys.exit(1)

from schemas.schema import (
    PDFToImageInput,
    PDFToImageOutput,
    PDFBatchInput,
    PDFBatchOutput
)


class PDFToImageConverter:
    """處理 PDF 轉圖片轉換操作的類別。"""

    def __init__(self, max_size: int = 1024, dpi: int = 200, fmt: str = "PNG"):
        """初始化 PDF 轉圖片轉換器。

        Args:
            dpi: 輸出圖片的解析度（預設：200）
            fmt: 輸出圖片格式（預設：PNG）
        """
        self.dpi = dpi
        self.fmt = fmt.upper()
        self.max_size = max_size

    def convert(
        self,
        pdf_path: str,
        output_dir: str,
        filename_prefix: Optional[str] = None
    ) -> PDFToImageOutput:
        """將 PDF 檔案轉換為圖片。

        Args:
            pdf_path: 輸入 PDF 檔案的路徑
            output_dir: 儲存輸出圖片的目錄
            filename_prefix: 輸出檔名的可選前綴

        Returns:
            包含轉換結果的 PDFToImageOutput 物件

        Raises:
            FileNotFoundError: 如果 PDF 檔案不存在
            ValueError: 如果無法轉換 PDF
        """
        pdf_path = Path(pdf_path)
        output_dir = Path(output_dir)

        # 驗證輸入
        if not pdf_path.exists():
            error_msg = f"找不到 PDF 檔案：{pdf_path}"
            return PDFToImageOutput(
                pdf_path=str(pdf_path),
                output_dir=str(output_dir),
                image_paths=[],
                total_pages=0,
                raw_pdf_text="",
                status='failed',
                error=error_msg
            )

        if not pdf_path.is_file():
            error_msg = f"路徑不是檔案：{pdf_path}"
            return PDFToImageOutput(
                pdf_path=str(pdf_path),
                output_dir=str(output_dir),
                image_paths=[],
                total_pages=0,
                raw_pdf_text="",
                status='failed',
                error=error_msg
            )

        # 建立輸出目錄
        output_dir.mkdir(parents=True, exist_ok=True)

        # 決定檔名前綴
        if filename_prefix is None:
            filename_prefix = pdf_path.stem

        print(f"正在將 {pdf_path.name} 轉換為圖片...")
        print(f"DPI：{self.dpi}，格式：{self.fmt}")

        try:
            # 開啟 PDF 檔案
            pdf_document = fitz.open(str(pdf_path))
            total_pages = len(pdf_document)

            # 根據 DPI 計算縮放因子
            # fitz 預設為 72 DPI，所以 zoom = 目標_dpi / 72
            zoom = self.dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)

            output_paths = []
            all_pdf_text = []

            # 將每一頁轉換為圖片
            for page_num in range(total_pages):
                page = pdf_document[page_num]

                # 將頁面文字抽取
                pdf_text = self._extract_pdf_text(page)
                all_pdf_text.append(pdf_text)

                # 將頁面渲染為像素圖
                pix = page.get_pixmap(matrix=mat)

                # 產生帶有頁碼的輸出檔名
                output_filename = f"{filename_prefix}_page_{page_num + 1:04d}.{self.fmt.lower()}"
                output_path = output_dir / output_filename

                # 將像素圖轉換為 PIL Image 以提供格式彈性
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                # 縮放
                w, h = img.size
                max_ = max(w, h)
                max__ = min(max_, self.max_size)
                scale = max__ / max_

                new_w = int(w * scale)
                new_h = int(h * scale)


                img = img.resize((new_w, new_h), Image.LANCZOS)

                # 以指定格式儲存圖片
                img.save(str(output_path), self.fmt)
                output_paths.append(str(output_path))

                print(f"已儲存第 {page_num + 1}/{total_pages} 頁：{output_path.name}")

            pdf_document.close()
            print(f"\n成功將 {total_pages} 頁轉換到 {output_dir}")

            return PDFToImageOutput(
                pdf_path=str(pdf_path),
                output_dir=str(output_dir),
                image_paths=output_paths,
                total_pages=total_pages,
                raw_pdf_text=all_pdf_text,
                status='success',
                error=None
            )

        except Exception as e:
            error_msg = f"轉換 PDF 失敗：{e}"
            return PDFToImageOutput(
                pdf_path=str(pdf_path),
                output_dir=str(output_dir),
                image_paths=[],
                total_pages=0,
                raw_pdf_text=[],
                status='failed',
                error=error_msg
            )

    def convert_batch(
        self,
        input_dir: str,
        output_dir: str,
        recursive: bool = False,
        filename_prefix: Optional[str] = None
    ) -> PDFBatchOutput:
        """將目錄中的所有 PDF 檔案轉換為圖片。

        Args:
            input_dir: 包含 PDF 檔案的目錄
            output_dir: 儲存輸出圖片的目錄
            recursive: 是否在子目錄中遞迴搜尋 PDF
            filename_prefix: 輸出檔名的可選前綴（預設：使用 PDF 檔名）

        Returns:
            包含批次轉換結果的 PDFBatchOutput 物件

        Raises:
            FileNotFoundError: 如果輸入目錄不存在
        """
        input_dir = Path(input_dir)
        output_dir = Path(output_dir)

        # 驗證輸入目錄
        if not input_dir.exists():
            raise FileNotFoundError(f"找不到輸入目錄：{input_dir}")

        if not input_dir.is_dir():
            raise ValueError(f"路徑不是目錄：{input_dir}")

        # 尋找所有 PDF 檔案
        if recursive:
            pdf_files = list(input_dir.rglob("*.pdf"))
        else:
            pdf_files = list(input_dir.glob("*.pdf"))

        if not pdf_files:
            print(f"在 {input_dir} 中找不到 PDF 檔案")
            return PDFBatchOutput(
                total=0,
                success=0,
                failed=0,
                results=[]
            )

        print(f"找到 {len(pdf_files)} 個要轉換的 PDF 檔案")
        print(f"輸出目錄：{output_dir}")
        print("=" * 60)

        results = []
        success_count = 0
        failed_count = 0

        # 轉換每個 PDF
        for idx, pdf_file in enumerate(pdf_files, start=1):
            print(f"\n[{idx}/{len(pdf_files)}] 處理中：{pdf_file.name}")

            # 為每個 PDF 的圖片建立子目錄
            pdf_output_dir = output_dir / pdf_file.stem

            # 將 PDF 轉換為圖片
            conversion_result = self.convert(
                pdf_path=str(pdf_file),
                output_dir=str(pdf_output_dir),
                filename_prefix=filename_prefix
            )
            results.append(conversion_result)
            # 檢查轉換狀態
            if conversion_result.status == 'success':
                success_count += 1
            else:
                failed_count += 1
                print(f"✗ 轉換 {pdf_file.name} 失敗：{conversion_result.error}")

        # 列印摘要
        print("\n" + "=" * 60)
        print("批次轉換摘要")
        print("=" * 60)
        print(f"總 PDF 數：{len(pdf_files)}")
        print(f"成功：{success_count}")
        print(f"失敗：{failed_count}")

        return PDFBatchOutput(
            total=len(pdf_files),
            success=success_count,
            failed=failed_count,
            results=results
        )

    def save_batch_output(self, batch_output: PDFBatchOutput, output_path: str) -> None:
        """將 PDFBatchOutput 儲存為 JSON 檔案

        Args:
            batch_output: PDFBatchOutput 物件
            output_path: JSON 檔案的輸出路徑
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(batch_output.to_dict(), f, ensure_ascii=False, indent=2)

        print(f"批次輸出已儲存至：{output_path}")

    def _extract_pdf_text(self, page):

        text = page.get_text()
        if len(text.strip()) == 0:
            print(f"無文字")
        else:
            print(f"包含文字")

        return text.strip()