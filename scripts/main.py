#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel Parser LLM + Augmenter Pipeline
將 Excel 檔案解析並生成增強查詢的完整流程
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import yaml
from tqdm import tqdm

# 添加父目錄到 Python 路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.parser.excel_parser_llm import ExcelParserLLM
from utils.augmenter.llm_augmenter import LLMAugmenter
from utils.schemas import GroundTruth, AugmenterInput


def load_config(config_path: Path) -> Dict[str, Any]:
    """
    載入 YAML 配置檔案

    Args:
        config_path: 配置檔案路徑

    Returns:
        配置字典
    """
    if not config_path.exists():
        raise FileNotFoundError(f"配置檔案不存在: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    return config


def main():
    """主程式流程"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 檢查命令列參數
    if len(sys.argv) < 2:
        print("使用方法: python scripts/main.py <配置檔案路徑>", file=sys.stderr)
        print("\n範例:")
        print("  python scripts/main.py config/config.example.yml")
        print("  python scripts/main.py config/config.openrouter.yml")
        sys.exit(1)

    # 載入配置檔案
    config_path = Path(sys.argv[1])

    try:
        config = load_config(config_path)
    except FileNotFoundError as e:
        print(f"錯誤：{e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"錯誤：無法讀取配置檔案 - {e}", file=sys.stderr)
        sys.exit(1)

    # 提取配置值
    input_file = Path(config['input']['file'])
    output_dir = Path(config['output']['dir']) if config['output']['dir'] else Path(f"results/pipeline_{timestamp}")
    skip_parser = config['options'].get('skip_parser', False)
    quiet = config['options'].get('quiet', False)

    # 驗證檔案路徑
    if not skip_parser and not input_file.exists():
        print(f"錯誤：檔案不存在 - {input_file}", file=sys.stderr)
        sys.exit(1)

    # 創建輸出目錄
    output_dir.mkdir(parents=True, exist_ok=True)

    # 設定各階段輸出路徑
    parsed_output_path = Path(config['output']['parsed_data']) if config['output']['parsed_data'] else output_dir / "parsed_data.json"
    augmenter_output_path = Path(config['output']['augmented_queries']) if config['output']['augmented_queries'] else output_dir / "augmented_queries.json"

    if not quiet:
        print("=" * 70)
        print("Excel Parser LLM + Augmenter Pipeline")
        print("=" * 70)
        print(f"輸入檔案: {input_file}")
        print(f"輸出目錄: {output_dir}")
        print(f"Parser 輸出: {parsed_output_path}")
        print(f"Augmenter 輸出: {augmenter_output_path}")
        print("\nParser LLM 設定:")
        print(f"  URL: {config['parser']['llm']['url']}")
        print(f"  Model: {config['parser']['llm']['model']}")
        print(f"  OpenRouter: {config['parser']['llm']['use_openrouter']}")
        print("\nAugmenter LLM 設定:")
        print(f"  URL: {config['augmenter']['llm']['url']}")
        print(f"  Model: {config['augmenter']['llm']['model']}")
        print(f"  OpenRouter: {config['augmenter']['llm']['use_openrouter']}")
        print(f"  Prompt: {config['augmenter']['prompt_name']}")
        print("=" * 70)

    try:
        # ==================== 步驟 1: Parser ====================
        if skip_parser:
            if not quiet:
                print("\n跳過 Parser 步驟，從已解析的檔案讀取...")

            if not parsed_output_path.exists():
                print(f"錯誤：找不到已解析的檔案 - {parsed_output_path}", file=sys.stderr)
                sys.exit(1)

            with open(parsed_output_path, 'r', encoding='utf-8') as f:
                result = json.load(f)

            if not quiet:
                print(f"  已載入 {len(result.get('cells', []))} 個儲存格")
        else:
            if not quiet:
                print("\n步驟 1/2: 使用 LLM 解析 Excel 檔案")
                print("-" * 70)

            parser_llm = ExcelParserLLM(
                vllm_url=config['parser']['llm']['url'],
                model=config['parser']['llm']['model'],
                api_key=config['parser']['llm']['api_key'],
                use_openrouter=config['parser']['llm']['use_openrouter'],
                max_retries=config['parser']['llm']['max_retries']
            )

            result = parser_llm.parse_excel_with_llm(input_file)

            parser_llm.save_result(result, parsed_output_path)

            if not quiet:
                print(f"\n解析結果摘要：")
                print(f"  標題: {result.get('title', 'N/A')}")
                print(f"  X 軸: {result.get('x-axis', 'N/A')}")
                print(f"  Y 軸: {result.get('y-axis', 'N/A')}")
                print(f"  重要儲存格數: {len(result.get('cells', []))}")

        # ==================== 轉換格式 ====================
        if not quiet:
            print("\n轉換為 AugmenterInput 格式...")

        inputs = ExcelParserLLM.transform_to_augmenterInput(result)

        if not quiet:
            print(f"  已轉換 {len(inputs)} 個儲存格")

        # ==================== 步驟 2: Augmenter ====================
        if not quiet:
            print("\n步驟 2/2: 使用 LLM 生成增強查詢")
            print("-" * 70)

        augmenter_keyword = LLMAugmenter(
            vllm_url=config['augmenter']['llm']['url'],
            model=config['augmenter']['llm']['model'],
            prompt_name=config['augmenter']['prompt_name'],
            api_key=config['augmenter']['llm']['api_key'],
            use_openrouter=config['augmenter']['llm']['use_openrouter']
        )

        results = []
        for idx, item in enumerate(tqdm(inputs, desc="生成查詢", disable=quiet)):
            # 共同欄位 ground_truth（必要）
            try:
                gt_raw = item["ground_truth"]
                ground_truth = GroundTruth(
                    file_name=gt_raw["file_name"],
                    item_id=gt_raw["item_id"],
                )
            except KeyError as e:
                print(f"警告：第 {idx} 筆資料缺少 ground_truth 欄位或其子欄位：{e}", file=sys.stderr)
                continue

            if "keyword" not in item or not isinstance(item["keyword"], dict):
                print(f"警告：第 {idx} 筆 keyword 模式需要 'keyword'（dict）欄位", file=sys.stderr)
                continue

            aug_in = AugmenterInput(
                keyword=item["keyword"],
                ground_truth=ground_truth,
                metadata=item.get("metadata", {})
            )
            results.append(augmenter_keyword.augment(aug_in))

        # 儲存結果
        augmenter_keyword.save_augment_results(results, str(augmenter_output_path))

        # ==================== 完成 ====================
        if not quiet:
            print("\n" + "=" * 70)
            print("處理完成！")
            print("=" * 70)
            print(f"總共處理: {len(results)} 筆資料")
            print(f"\n輸出檔案:")
            print(f"  1. Parser 輸出: {parsed_output_path}")
            print(f"  2. Augmenter 輸出: {augmenter_output_path}")
            print("=" * 70)

    except KeyboardInterrupt:
        print("\n\n使用者中斷執行", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n錯誤：{e}", file=sys.stderr)
        if not quiet:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
