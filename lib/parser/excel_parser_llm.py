#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel Parser with LLM
使用 LLM 來解析 Excel 檔案，提取標題、軸意義和儲存格資訊
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import requests
import openpyxl
from openpyxl.worksheet.worksheet import Worksheet

# 導入 PromptManager
from lib.prompt.prompt_manager import PromptManager


class ExcelParserLLM:
    """使用 LLM 解析 Excel 的模組"""

    def __init__(
        self,
        vllm_url: str,
        model: str,
        api_key: Optional[str] = None,
        use_openrouter: bool = False,
        max_retries: int = 3,
        prompt_key: str = "excel_parser",
        prompt_corpus_path: str = "configs/prompt_corpus.json"
    ):
        """
        初始化 Excel Parser with LLM

        Args:
            vllm_url: LLM API URL
            model: 模型名稱
            api_key: API 金鑰（OpenRouter 需要）
            use_openrouter: 是否使用 OpenRouter API（預設：False）
            max_retries: 最大重試次數
            prompt_key: prompt_corpus 中的 key（預設：excel_parser）
            prompt_corpus_path: prompt_corpus.json 的路徑（預設：configs/prompt_corpus.json）
        """
        self.vllm_url = vllm_url.rstrip('/')
        self.model = model
        self.api_key = api_key
        self.use_openrouter = use_openrouter
        self.max_retries = max_retries
        self.session = requests.Session()

        # 初始化 PromptManager
        self.prompt_manager = PromptManager(
            prompt_key=prompt_key,
            prompt_corpuse_path=prompt_corpus_path
        )

    def get_column_name(self, col_index: int) -> str:
        """
        將欄位索引轉換為欄位名稱 (A, B, C, ..., AA, AB, ...)

        Args:
            col_index: 欄位索引 (1-based)

        Returns:
            欄位名稱字串
        """
        column_name = ""
        while col_index > 0:
            col_index -= 1
            column_name = chr(col_index % 26 + ord('A')) + column_name
            col_index //= 26
        return column_name

    def load_excel(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        載入 Excel 檔案並取得基本結構

        Args:
            file_path: Excel 檔案路徑

        Returns:
            包含檔案資訊和儲存格資料的字典
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"檔案不存在: {file_path}")

        if file_path.suffix not in ['.xlsx', '.xlsm', '.xltx', '.xltm']:
            raise ValueError(f"不支援的檔案格式: {file_path.suffix}")

        workbook = openpyxl.load_workbook(file_path, data_only=True)

        # 取得第一個工作表（通常資料在第一個表）
        sheet = workbook.active
        sheet_name = sheet.title

        # 取得所有儲存格資料
        cells_data = []
        for row in sheet.iter_rows():
            for cell in row:
                if cell.value is not None:
                    cell_info = {
                        "row": cell.row,
                        "col": cell.column,
                        "col_name": self.get_column_name(cell.column),
                        "address": f"{self.get_column_name(cell.column)}{cell.row}",
                        "value": str(cell.value)
                    }
                    cells_data.append(cell_info)

        # 取得表格範圍資訊
        max_row = sheet.max_row
        max_col = sheet.max_column

        return {
            "file_name": file_path.name,
            "file_path": str(file_path.absolute()),
            "sheet_name": sheet_name,
            "max_row": max_row,
            "max_col": max_col,
            "total_cells": len(cells_data),
            "cells": cells_data
        }

    def create_excel_context(self, excel_data: Dict[str, Any]) -> str:
        """
        創建用於 LLM 的 Excel 上下文

        Args:
            excel_data: Excel 資料字典

        Returns:
            格式化的上下文字串
        """
        context = f"檔案名稱：{excel_data['file_name']}\n"
        context += f"工作表名稱：{excel_data['sheet_name']}\n"
        context += f"表格大小：{excel_data['max_row']} 列 x {excel_data['max_col']} 欄\n\n"
        context += "儲存格內容：\n"

        # 將儲存格資料格式化為易讀的表格形式
        for cell in excel_data['cells'][:100]:  # 限制顯示前 100 個儲存格避免太長
            context += f"{cell['address']}: {cell['value']}\n"

        if len(excel_data['cells']) > 100:
            context += f"\n... 還有 {len(excel_data['cells']) - 100} 個儲存格\n"

        return context

    def create_prompt(self, excel_context: str) -> str:
        """
        創建用於 LLM 的提示詞（透過 PromptManager 管理）

        Args:
            excel_context: Excel 上下文資訊

        Returns:
            完整的提示詞
        """
        return self.prompt_manager.generate_prompt_text(context=excel_context)

    def call_llm(self, prompt: str) -> Dict[str, Any]:
        """
        呼叫 LLM API 進行分析

        Args:
            prompt: 提示詞

        Returns:
            LLM 回應的 JSON 結果
        """
        headers = {"Content-Type": "application/json"}
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
            "max_tokens": 4096,
            "temperature": 0.3,  # 降低溫度以獲得更穩定的輸出
            "top_p": 0.9
        }

        for attempt in range(self.max_retries):
            try:
                response = self.session.post(
                    f"{self.vllm_url}",
                    headers=headers,
                    json=data,
                    timeout=120
                )

                if response.status_code == 200:
                    content_type = response.headers.get('Content-Type', '')

                    if 'application/json' not in content_type:
                        print(f"警告：API 返回的不是 JSON 格式（Content-Type: {content_type}）")
                        raise ValueError(f"API 返回非 JSON 格式")

                    result = response.json()

                    if "choices" not in result or len(result["choices"]) == 0:
                        raise ValueError("API 回應缺少 'choices' 欄位")

                    generated_text = result["choices"][0]["message"]["content"].strip()

                    # 解析 LLM 回應的 JSON
                    return self.parse_llm_response(generated_text)
                else:
                    print(f"API 呼叫失敗（嘗試 {attempt + 1}/{self.max_retries}）：狀態碼 {response.status_code}")
                    print(f"回應內容：{response.text[:500]}")

            except requests.exceptions.RequestException as e:
                print(f"網路錯誤（嘗試 {attempt + 1}/{self.max_retries}）：{e}")

            if attempt < self.max_retries - 1:
                time.sleep(2 ** attempt)  # 指數退避

        raise Exception("LLM API 呼叫失敗，已達最大重試次數")

    def parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """
        解析 LLM 回應的文字，提取 JSON

        Args:
            response_text: LLM 回應的原始文字

        Returns:
            解析後的 JSON 物件
        """
        # 嘗試找到 JSON 區塊
        import re

        # 移除 markdown 程式碼區塊標記
        response_text = re.sub(r'```json\s*', '', response_text)
        response_text = re.sub(r'```\s*', '', response_text)

        # 嘗試解析 JSON
        try:
            return json.loads(response_text.strip())
        except json.JSONDecodeError as e:
            print(f"JSON 解析錯誤：{e}")
            print(f"回應文字：{response_text}")

            # 嘗試找到 JSON 物件
            match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass

            raise ValueError("無法從 LLM 回應中解析 JSON")

    def parse_excel_with_llm(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        使用 LLM 解析 Excel 檔案的完整流程

        Args:
            file_path: Excel 檔案路徑

        Returns:
            包含標題、軸意義和儲存格資訊的字典
        """
        print(f"步驟 0：載入 Excel 檔案 - {file_path}")
        excel_data = self.load_excel(file_path)
        print(f"  已載入 {excel_data['total_cells']} 個儲存格")

        print(f"\n步驟 1：使用 LLM 分析 Excel 內容...")
        excel_context = self.create_excel_context(excel_data)
        prompt = self.create_prompt(excel_context)

        llm_result = self.call_llm(prompt)
        print(f"  LLM 分析完成")

        # 合併原始資料和 LLM 分析結果
        result = {
            "file_name": excel_data['file_name'],
            "file_path": excel_data['file_path'],
            "sheet_name": excel_data['sheet_name'],
            "title": llm_result.get("title", ""),
            "x-axis": llm_result.get("x-axis", ""),
            "y-axis": llm_result.get("y-axis", ""),
            "cells": llm_result.get("cells", []),
            "raw_excel_data": {
                "max_row": excel_data['max_row'],
                "max_col": excel_data['max_col'],
                "total_cells": excel_data['total_cells']
            }
        }

        return result

    def batch_parse_excel_with_llm(self, file_paths: List[Union[str, Path]]) -> List[Dict[str, Any]]:
        """
        批次使用 LLM 解析多個 Excel 檔案

        Args:
            file_paths: Excel 檔案路徑列表

        Returns:
            包含每個檔案解析結果的列表
        """
        results = []
        total_files = len(file_paths)

        print(f"\n開始批次處理 {total_files} 個 Excel 檔案...")
        print("=" * 70)

        for idx, file_path in enumerate(file_paths, 1):
            try:
                print(f"\n處理檔案 [{idx}/{total_files}]: {file_path}")
                print("-" * 70)

                result = self.parse_excel_with_llm(file_path)
                results.append(result)

                print(f"✓ 檔案 {idx} 處理完成")

            except Exception as e:
                print(f"✗ 檔案 {idx} 處理失敗: {e}")
                # 將錯誤資訊也加入結果
                results.append({
                    "file_name": Path(file_path).name,
                    "file_path": str(Path(file_path).absolute()),
                    "error": str(e),
                    "success": False
                })
                continue

        print("\n" + "=" * 70)
        print(f"批次處理完成！成功: {sum(1 for r in results if r.get('success', True) != False)}/{total_files}")

        return results

    def save_result(self, result: Dict[str, Any], output_path: Union[str, Path]) -> None:
        """
        儲存解析結果到 JSON 檔案

        Args:
            result: 解析結果
            output_path: 輸出檔案路徑
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"\n已儲存結果至: {output_path}")

    @staticmethod
    def transform_to_augmenterInput(
        excel_parser_output: Dict[str, Any],
        cell_index: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        將 Excel Parser LLM 的輸出轉換為 LLMAugmenterInput 格式

        Args:
            excel_parser_output: Excel Parser LLM 的輸出 JSON
            cell_index: 要轉換的儲存格索引（預設：None，表示轉換所有儲存格）
                       如果設為整數，則只轉換該索引的儲存格

        Returns:
            List[Dict[str, Any]]: 轉換後的 LLMAugmenterInput 格式列表
                每個字典包含 'source' 欄位（對應原本的 keyword）和 'source_path' 欄位

        Example:
            >>> import json
            >>> from pathlib import Path
            >>> with open('parsed_data.json', 'r', encoding='utf-8') as f:
            ...     parsed_data = json.load(f)
            >>> inputs = ExcelParserLLM.transform_to_augmenterInput(parsed_data)
        """
        results = []

        # 提取基本資訊
        title = excel_parser_output.get("title", "")
        x_axis = excel_parser_output.get("x-axis", "")
        y_axis = excel_parser_output.get("y-axis", "")
        cells = excel_parser_output.get("cells", [])
        file_path = excel_parser_output.get("file_path", "")

        # 如果指定了 cell_index，只處理該儲存格
        if cell_index is not None and isinstance(cell_index, int):
            if 0 <= cell_index < len(cells):
                cells_to_process = [cells[cell_index]]
            else:
                raise IndexError(f"cell_index {cell_index} 超出範圍（總共 {len(cells)} 個儲存格）")
        else:
            cells_to_process = cells

        # 轉換每個儲存格
        for cell in cells_to_process:
            x_axis_meaning = cell.get("x-axis id 意思", "")
            y_axis_meaning = cell.get("y-axis id 意思", "")
            value = cell.get("值", "")

            # 構建 source（原本的 keyword）
            source = {
                "table_title": title,
                "table's x-axis": x_axis,
                "table's y-axis": y_axis,
                "cell's x-axis id 意思": x_axis_meaning,
                "cell's y-axis id 意思": y_axis_meaning,
                "值": str(value)
            }

            # 創建 LLMAugmenterInput 格式的字典
            augmenter_input = {
                "source": source,
                "source_path": file_path
            }

            results.append(augmenter_input)

        return results


def main():
    """
    主程式 - CLI 介面
    """
    parser = argparse.ArgumentParser(
        description="Excel Parser with LLM - 使用 LLM 解析 Excel 檔案",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  # 使用本地 vLLM
  python excel_parser_llm.py --file 表12-1.xlsx --vllm-url http://192.168.1.79:3472 --model gemma-12b-8bit

  # 使用 OpenRouter
  python excel_parser_llm.py --file 表12-1.xlsx --use-openrouter --api-key YOUR_API_KEY --vllm-url https://openrouter.ai --model google/gemini-2.0-flash-exp:free

  # 指定輸出路徑
  python excel_parser_llm.py --file 表12-1.xlsx --output result.json --vllm-url http://192.168.1.79:3472 --model gemma-12b-8bit
        """
    )

    parser.add_argument(
        "--file",
        "-f",
        type=str,
        required=True,
        help="要解析的 Excel 檔案路徑"
    )

    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="輸出 JSON 檔案路徑（預設：data/parsed_data/{檔名}.json）"
    )

    parser.add_argument(
        "--vllm-url",
        default="http://192.168.1.79:3472",
        help="LLM API URL（預設：http://192.168.1.79:3472）"
    )

    parser.add_argument(
        "--model",
        default="gemma-12b-8bit",
        help="模型名稱（預設：gemma-12b-8bit）"
    )

    parser.add_argument(
        "--api-key",
        default=None,
        help="API 金鑰（OpenRouter 使用）"
    )

    parser.add_argument(
        "--use-openrouter",
        action="store_true",
        help="使用 OpenRouter API"
    )

    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="最大重試次數（預設：3）"
    )

    args = parser.parse_args()

    # 檢查檔案是否存在
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"錯誤：檔案不存在 - {file_path}", file=sys.stderr)
        sys.exit(1)

    # 設定輸出路徑
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = Path("data/parsed_data") / f"{file_path.stem}.json"

    print("=" * 70)
    print("Excel Parser with LLM")
    print("=" * 70)

    try:
        # 初始化解析器
        parser_llm = ExcelParserLLM(
            vllm_url=args.vllm_url,
            model=args.model,
            api_key=args.api_key,
            use_openrouter=args.use_openrouter,
            max_retries=args.max_retries
        )

        # 解析 Excel
        result = parser_llm.parse_excel_with_llm(file_path)

        # 顯示結果摘要
        print("\n" + "=" * 70)
        print("解析結果摘要：")
        print("=" * 70)
        print(f"標題：{result['title']}")
        print(f"X 軸意義：{result['x-axis']}")
        print(f"Y 軸意義：{result['y-axis']}")
        print(f"重要儲存格數量：{len(result['cells'])}")

        # 儲存結果
        parser_llm.save_result(result, output_path)

        print("\n" + "=" * 70)
        print("完成！")
        print("=" * 70)

    except Exception as e:
        print(f"\n錯誤：{e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
