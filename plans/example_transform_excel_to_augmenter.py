#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel Parser LLM 輸出轉換為 AugmenterInput 的範例

此腳本展示如何將 Excel Parser LLM 的輸出轉換為 Augmenter 可用的格式
"""

import json
from pathlib import Path
from utils.parser.excel_parser_llm import ExcelParserLLM


def main():
    # 範例 1：從檔案讀取並轉換所有儲存格
    print("=" * 70)
    print("範例 1：轉換所有儲存格")
    print("=" * 70)

    # 讀取 Excel Parser LLM 的輸出
    input_file = Path("data/parsed_data/youtube_100_records.json")

    if not input_file.exists():
        print(f"錯誤：找不到檔案 {input_file}")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        parsed_excel = json.load(f)

    # 轉換為 AugmenterInput 格式
    augmenter_inputs = ExcelParserLLM.transform_to_augmenterInput(parsed_excel)

    print(f"共轉換了 {len(augmenter_inputs)} 個儲存格")
    print(f"\n第一個儲存格的轉換結果：")
    print(json.dumps(augmenter_inputs[0], ensure_ascii=False, indent=2))

    # 儲存轉換結果
    output_file = Path("data/augmenter_input/youtube_100_records_augmenter_input.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # augmenter_inputs 已經是 JSON 可序列化的格式
    output_data = augmenter_inputs

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\n已儲存至：{output_file}")

    # 範例 2：只轉換特定索引的儲存格
    print("\n" + "=" * 70)
    print("範例 2：只轉換第 7 個儲存格")
    print("=" * 70)

    single_cell = ExcelParserLLM.transform_to_augmenterInput(parsed_excel, cell_index=6)
    print(json.dumps(single_cell[0], ensure_ascii=False, indent=2))

    # 範例 3：顯示預期的輸出格式
    print("\n" + "=" * 70)
    print("範例 3：預期的輸出格式")
    print("=" * 70)

    expected_format = {
        "keyword": {
            "table_title": "YouTube 影音資料紀錄",
            "table's x-axis": "欄位標題（影片屬性）",
            "table's y-axis": "影片紀錄編號（video_id）",
            "cell's x-axis id 意思": "觀看次數",
            "cell's y-axis id 意思": "第七筆影片紀錄（Cooking Pasta）",
            "值": "1754397"
        },
        "ground_truth": {
            "file_name": "youtube_100_records.xlsx",
            "item_id": [7]
        },
        "metadata": {
            "x-axis id": "E",
            "y-axis id": "7",
            "source": "excel_parser_llm"
        }
    }

    print(json.dumps(expected_format, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
