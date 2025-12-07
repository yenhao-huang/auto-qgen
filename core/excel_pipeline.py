#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel Augment Service - 將 Excel 解析與增強查詢封裝為 function
提供 run() 函數執行完整流程：parser + transform + augment + output
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import yaml
from tqdm import tqdm
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.parser.excel_parser_llm import ExcelParserLLM
from lib.augment.llm_augmenter import LLMAugmenter
from schemas.schema import LLMAugmenterInput, VLLMPayload, OpenRouterPayload, AutoGenOutput, AutoGenRawOutput


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


def excel_parse(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    執行 Excel 解析流程

    流程:
        1. Parser: 解析 Excel 檔案
        2. Transform: 轉換為 AugmenterInput 格式
        3. Output: 儲存結果

    Args:
        config: 配置字典，包含 parser、input、output 等設定
            必要欄位:
                - input.file_path: 輸入 Excel 檔案路徑
            可選欄位:
                - output.dir: 輸出目錄（預設使用 timestamp 目錄）
                - input.skip_parser: 是否跳過 Parser 步驟（預設 False）
                - input.parsed_data_path: 已解析的數據路徑
                - verbose: 是否顯示詳細訊息（預設 True）

    Returns:
        Dict 包含:
            - success: bool, 是否成功
            - parsed_data_path: str, Parser 輸出路徑
            - parsed_data: Dict, 解析後的數據
            - augmenter_inputs: List, 轉換為 AugmenterInput 格式的列表
            - total_count: int, 處理的數據筆數
            - error: str (可選), 錯誤訊息
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 從 config 讀取參數
        input_file = Path(config['input']['file_path'])
        skip_parser = config.get('input', {}).get('skip_parser', False)
        parsed_data_path = config.get('input', {}).get('parsed_data_path')
        if parsed_data_path:
            parsed_data_path = Path(parsed_data_path)
        quiet = not config.get('verbose', True)

        # 設定輸出目錄
        output_dir = config.get('output', {}).get('dir')
        if output_dir is None:
            output_dir = Path(f"results/parser_{timestamp}")
        else:
            output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 設定 Parser 輸出路徑
        parsed_output_path = output_dir / "parsed_data.json"

        if not quiet:
            print("=" * 70)
            print("Excel Parser LLM Service")
            print("=" * 70)
            print(f"輸入檔案: {input_file}")
            print(f"輸出目錄: {output_dir}")
            print("=" * 70)

        # ==================== 步驟 1: Parser ====================
        if skip_parser:
            if not quiet:
                print("\n跳過 Parser 步驟，從已解析的檔案讀取...")

            if parsed_data_path is None or not parsed_data_path.exists():
                raise FileNotFoundError(f"找不到已解析的檔案 - {parsed_data_path}")

            with open(parsed_data_path, 'r', encoding='utf-8') as f:
                result = json.load(f)

            if not quiet:
                print(f"  已載入 {len(result.get('cells', []))} 個儲存格")
        else:
            # 驗證輸入檔案
            if not input_file.exists():
                raise FileNotFoundError(f"輸入檔案不存在 - {input_file}")

            if not quiet:
                print("\n步驟 1/2: 使用 LLM 解析 Excel 檔案")
                print("-" * 70)

            # 初始化 Parser LLM
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

        # ==================== 步驟 2: Transform ====================
        if not quiet:
            print("\n步驟 2/2: 轉換為 AugmenterInput 格式")
            print("-" * 70)

        inputs = ExcelParserLLM.transform_to_augmenterInput(result)

        if not quiet:
            print(f"  已轉換 {len(inputs)} 個儲存格")

        # ==================== 完成 ====================
        if not quiet:
            print("\n" + "=" * 70)
            print("Parser 處理完成！")
            print("=" * 70)
            print(f"總共處理: {len(inputs)} 筆資料")
            print(f"\n輸出檔案:")
            print(f"  Parser 輸出: {parsed_output_path}")
            print("=" * 70)

        return {
            "success": True,
            "parsed_data_path": str(parsed_output_path.resolve()),
            "parsed_data": result,
            "augmenter_inputs": inputs,
            "total_count": len(inputs)
        }

    except Exception as e:
        error_msg = f"Parser 處理失敗: {str(e)}"
        if not quiet:
            print(f"\n錯誤：{error_msg}", file=sys.stderr)
            import traceback
            traceback.print_exc()

        return {
            "success": False,
            "error": error_msg,
            "total_count": 0
        }


def augment(config: Dict[str, Any], augmenter_inputs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    執行數據增強流程

    流程:
        1. Augment: 使用 LLM 生成增強查詢
        2. Output: 儲存結果

    Args:
        config: 配置字典，包含 augmenter、output 等設定
            必要欄位:
                - mode: 使用的模式 (vllm 或 openrouter)
                - augmenter: Augmenter 設定
            可選欄位:
                - output.dir: 輸出目錄（預設使用 timestamp 目錄）
                - verbose: 是否顯示詳細訊息（預設 True）
        augmenter_inputs: 從 parser() 函數返回的 augmenter_inputs

    Returns:
        Dict 包含:
            - success: bool, 是否成功
            - augmented_queries_path: str, Augmenter 輸出路徑
            - augmented_queries: List, 增強查詢結果列表
            - total_count: int, 處理的數據筆數
            - error: str (可選), 錯誤訊息
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 從 config 讀取參數
        quiet = not config.get('verbose', True)
        augmenter_config = config.get('augmenter')
        mode = augmenter_config.get('mode')

        # 設定輸出目錄
        output_dir = config.get('output', {}).get('dir')
        if output_dir is None:
            output_dir = Path(f"results/augmenter_{timestamp}")
        else:
            output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 設定 Augmenter 輸出路徑
        augmenter_output_path = output_dir / "augmented_queries.json"

        if not quiet:
            print("=" * 70)
            print("LLM Augmenter Service")
            print("=" * 70)
            print(f"輸出目錄: {output_dir}")
            print("=" * 70)

        # ==================== 步驟 1: Augment ====================
        if not quiet:
            print("\n步驟 1/2: 使用 LLM 生成增強查詢")
            print("-" * 70)

        # 根據模式建立 payload
        if not quiet:
            print(f"\n初始化 LLM Augmenter...")
            
        # 初始化 Augmenter LLM
        if mode == "vllm":
            vllm_config = augmenter_config['vllm']
            payload = {
                "vllm_url": vllm_config['url'],
                "model_name": vllm_config['model_name'],
                "max_tokens": vllm_config.get('max_tokens', 18000),
                "temperature": vllm_config.get('temperature', 0.7),
                "top_p": vllm_config.get('top_p', 0.9),
                "frequency_penalty": vllm_config.get('frequency_penalty', 0.1),
                "presence_penalty": vllm_config.get('presence_penalty', 0.1),
                "is_thinking_mode": vllm_config.get('is_thinking_mode', False),
                "limit_llmoutput_scheme": vllm_config.get('limit_llmoutput_scheme', False),
            }
        elif mode == "openrouter":
            openrouter_config = augmenter_config['openrouter']
            payload = {
                "api_key": openrouter_config['api_key'],
                "url": openrouter_config['url'],
                "model_name": openrouter_config['model_name'],
                "max_tokens": openrouter_config.get('max_tokens', 18000),
                "temperature": openrouter_config.get('temperature', 0.7),
                "top_p": openrouter_config.get('top_p', 0.9),
                "frequency_penalty": openrouter_config.get('frequency_penalty', 0.1),
                "presence_penalty": openrouter_config.get('presence_penalty', 0.1),
                "is_thinking_mode": openrouter_config.get('is_thinking_mode', False),
            }
        else:
            raise ValueError(f"不支援的模式：{mode}")

        augmenter_llm = LLMAugmenter(
            mode=mode,
            payload=payload,
            prompt_name=config['augmenter'].get('prompt_name', 'default'),
            verify_connection=False
        )

        results = []
        raw_outputs = []
        for idx, item in enumerate(tqdm(augmenter_inputs, desc="生成查詢", disable=quiet)):
            try:
                if "source" not in item or not isinstance(item["source"], dict):
                    if not quiet:
                        print(f"警告：第 {idx} 筆缺少 'source' 欄位", file=sys.stderr)
                    continue

                # 建立 LLMAugmenterInput
                aug_input = LLMAugmenterInput(source=item["source"])

                # 執行 augment
                aug_output = augmenter_llm.augment(aug_input)

                # 組合 AutoGenOutput（用於主輸出）
                # 將 source 轉換為文字格式作為 ocr_text
                ocr_text = json.dumps(item["source"], ensure_ascii=False)
                result = AutoGenOutput(
                    source_path=item.get("source_path", ""),
                    ocr_text=ocr_text,
                    questions=aug_output.augmented_queries,
                )
                results.append(result.to_dict())

                # 組合 AutoGenRawOutput（用於原始回應）
                raw_output = AutoGenRawOutput(
                    source_path=item.get("source_path", ""),
                    mode=mode,
                    model_name=payload.get('model_name', ''),
                    ocr_text=ocr_text,
                    raw_response=aug_output.raw_response
                )
                raw_outputs.append(raw_output.to_dict())

            except KeyError as e:
                if not quiet:
                    print(f"警告：第 {idx} 筆資料缺少必要欄位：{e}", file=sys.stderr)
                continue
            except Exception as e:
                if not quiet:
                    print(f"警告：第 {idx} 筆資料處理失敗：{e}", file=sys.stderr)
                continue

        # ==================== 步驟 2: Output ====================
        # 儲存主結果到 JSON 檔案
        with open(augmenter_output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        # 儲存原始回應資料
        raw_output_path = str(augmenter_output_path).replace('.json', '_raw_responses.json')
        with open(raw_output_path, 'w', encoding='utf-8') as f:
            json.dump(raw_outputs, f, ensure_ascii=False, indent=2)

        # ==================== 完成 ====================
        if not quiet:
            print("\n" + "=" * 70)
            print("Augmenter 處理完成！")
            print("=" * 70)
            print(f"總共處理: {len(results)} 筆資料")
            print(f"\n輸出檔案:")
            print(f"  1. Augmenter 輸出: {augmenter_output_path}")
            print(f"  2. 原始回應輸出: {raw_output_path}")
            print("=" * 70)

        return {
            "success": True,
            "augmented_queries_path": str(augmenter_output_path.resolve()),
            "raw_responses_path": str(Path(raw_output_path).resolve()),
            "augmented_queries": results,
            "raw_responses": raw_outputs,
            "total_count": len(results)
        }

    except Exception as e:
        error_msg = f"Augmenter 處理失敗: {str(e)}"
        if not quiet:
            print(f"\n錯誤：{error_msg}", file=sys.stderr)
            import traceback
            traceback.print_exc()

        return {
            "success": False,
            "error": error_msg,
            "total_count": 0
        }


def run(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    執行完整的數據增強流程（組合 parser + augment）

    流程:
        1. Parser: 解析 Excel 檔案
        2. Transform: 轉換為 AugmenterInput 格式
        3. Augment: 使用 LLM 生成增強查詢
        4. Output: 儲存結果

    Args:
        config: 配置字典，包含 parser、augmenter、input、output 等設定
            必要欄位:
                - input.file_path: 輸入 Excel 檔案路徑
            可選欄位:
                - output.dir: 輸出目錄（預設使用 timestamp 目錄）
                - input.skip_parser: 是否跳過 Parser 步驟（預設 False）
                - input.parsed_data_path: 已解析的數據路徑
                - verbose: 是否顯示詳細訊息（預設 True）

    Returns:
        Dict 包含:
            - success: bool, 是否成功
            - parsed_data_path: str, Parser 輸出路徑
            - augmented_queries_path: str, Augmenter 輸出路徑
            - augmented_queries: List, 增強查詢結果列表
            - total_count: int, 處理的數據筆數
            - error: str (可選), 錯誤訊息
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        quiet = not config.get('verbose', True)

        # 設定統一的輸出目錄
        output_dir = config.get('output', {}).get('dir')
        if output_dir is None:
            output_dir = Path(f"results/pipeline_{timestamp}")
        else:
            output_dir = Path(output_dir)

        # 更新 config 使用統一的輸出目錄
        if 'output' not in config:
            config['output'] = {}
        config['output']['dir'] = str(output_dir)

        if not quiet:
            print("=" * 70)
            print("Excel Parser LLM + Augmenter Service")
            print("=" * 70)

        # ==================== 執行 Parser ====================
        parser_result = excel_parse(config)

        if not parser_result['success']:
            return parser_result

        # ==================== 執行 Augment ====================
        augment_result = augment(config, parser_result['augmenter_inputs'])

        if not augment_result['success']:
            return augment_result

        # ==================== 完成 ====================
        if not quiet:
            print("\n" + "=" * 70)
            print("完整流程處理完成！")
            print("=" * 70)
            print(f"總共處理: {augment_result['total_count']} 筆資料")
            print(f"\n輸出檔案:")
            print(f"  1. Parser 輸出: {parser_result['parsed_data_path']}")
            print(f"  2. Augmenter 輸出: {augment_result['augmented_queries_path']}")
            print(f"  3. 原始回應輸出: {augment_result['raw_responses_path']}")
            print("=" * 70)

        return {
            "success": True,
            "parsed_data_path": parser_result['parsed_data_path'],
            "augmented_queries_path": augment_result['augmented_queries_path'],
            "raw_responses_path": augment_result['raw_responses_path'],
            "augmented_queries": augment_result['augmented_queries'],
            "raw_responses": augment_result['raw_responses'],
            "total_count": augment_result['total_count']
        }

    except Exception as e:
        error_msg = f"處理失敗: {str(e)}"
        if not quiet:
            print(f"\n錯誤：{error_msg}", file=sys.stderr)
            import traceback
            traceback.print_exc()

        return {
            "success": False,
            "error": error_msg,
            "total_count": 0
        }


if __name__ == "__main__":
    """
    使用範例

    執行方式:
        python core/excel_augment.py
        python core/excel_augment.py --config configs/custom_config.yml
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Excel Augment Service - 完整的 Excel 解析與增強查詢流程",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
    # 使用預設配置檔
    python core/excel_augment.py

    # 使用自訂配置檔
    python core/excel_augment.py --config configs/my_config.yml
        """
    )
    parser.add_argument(
        "--config", "-c",
        type=str,
        default="configs/excel_augment.example.yml",
        help="配置檔案路徑 (預設: configs/excel_augment.example.yml)"
    )

    args = parser.parse_args()

    # 載入配置
    config_path = Path(args.config)

    if not config_path.exists():
        print(f"錯誤：配置檔案不存在 - {config_path}")
        print(f"\n請建立配置檔案或使用 --config 指定正確的配置檔路徑")
        sys.exit(1)

    config = load_config(config_path)

    # 執行流程
    result = run(config=config)

    # 顯示結果
    if result["success"]:
        print(f"\n處理數量: {result['total_count']}")
        print(f"Parser 輸出: {result['parsed_data_path']}")
        print(f"Augmenter 輸出: {result['augmented_queries_path']}")
    else:
        print(f"\n執行失敗: {result.get('error', '未知錯誤')}")
        sys.exit(1)
