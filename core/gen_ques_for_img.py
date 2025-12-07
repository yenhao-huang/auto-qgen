#!/usr/bin/env python3
"""
生成問題腳本
從 OCR 資料生成問題，用於 benchmark 測試
"""
import sys
from pathlib import Path

# 將專案根目錄加入 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import json
import argparse
from typing import List, Dict, Any
import yaml
from tqdm import tqdm

from lib.augment.llm_augmenter import LLMAugmenter
from schemas.schema import LLMAugmenterInput, AutoGenRawOutput, AutoGenOutput


def load_config(config_path: str) -> Dict[str, Any]:
    """載入配置文件

    Args:
        config_path: 配置文件路徑

    Returns:
        配置字典
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config


def load_ocr_json(input_path: str) -> Dict[str, Any]:
    """載入 OCR JSON 資料

    Args:
        input_path: 輸入 JSON 檔案路徑

    Returns:
        JSON 資料字典
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def save_benchmark(output_path: str, results: List[Dict[str, Any]]) -> None:
    """儲存 Benchmark 結果

    Args:
        output_path: 輸出 JSON 檔案路徑
        results: Benchmark 結果列表
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"✓ 已保存 {len(results)} 筆 Benchmark 資料到：{output_file}")


def save_raw_responses(output_path: str, raw_outputs: List[Dict[str, Any]]) -> None:
    """儲存 LLM 原始回應資料

    Args:
        output_path: 輸出 JSON 檔案路徑
        raw_outputs: LLM 原始輸出列表
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(raw_outputs, f, ensure_ascii=False, indent=2)

    print(f"✓ 已保存 {len(raw_outputs)} 筆 LLM 原始回應到：{output_file}")


def gen_ques(config_path: str = None):
    """主函數

    Args:
        config_path: 配置文件路徑，如果為 None 則從命令列參數讀取
    """
    # 如果沒有提供 config_path，則從命令列參數讀取
    if config_path is None:
        parser = argparse.ArgumentParser(description='從 OCR 資料生成問題')
        parser.add_argument(
            '--config',
            type=str,
            default='configs/gen_ques_config.yml',
            help='配置文件路徑（預設：configs/gen_ques_config.yml）'
        )
        args = parser.parse_args()
        config_path = args.config

    # 1. 載入配置文件
    print(f"載入配置文件：{config_path}")
    config = load_config(config_path)

    input_path = config['input']
    output_dir = config['output_dir']
    output_path = str(Path(output_dir) / "augmented_queries.json")
    mode = config['mode']

    print(f"輸入檔案：{input_path}")
    print(f"輸出檔案：{output_path}")
    print(f"模式：{mode}")

    # 2. 載入 OCR data
    print(f"\n載入 OCR 資料...")
    ocr_data = load_ocr_json(input_path)
    all_examples = ocr_data.get('results', [])
    print(f"總共有 {len(all_examples)} 筆資料")

    # 3. 初始化 LLMAugmenter
    print(f"\n初始化 LLM Augmenter...")
    if mode == "vllm":
        vllm_config = config['vllm']
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
        openrouter_config = config['openrouter']
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

    # 顯示 payload 資訊
    print(f"\nPayload 配置：")
    for key, value in payload.items():
        # 隱藏 API key 的部分內容
        if key == "api_key" and value:
            masked_value = value[:8] + "..." if len(value) > 8 else "***"
            print(f"  - {key}: {masked_value}")
        else:
            print(f"  - {key}: {value}")

    augmenter = LLMAugmenter(
        mode=mode,
        payload=payload,
        prompt_name=config.get('prompt_name', 'default'),
        verify_connection=config.get('verify_connection', True)
    )

    # 4. 處理每筆資料
    print(f"\n開始生成問題...")
    results = []
    raw_outputs = []

    for idx, example in enumerate(tqdm(all_examples, desc="生成問題"), 1):
        # 印出範例資訊
        print(f"\n=== Example {idx} ===")
        print(f"圖片名稱: {example['image_url'].split('/')[-1]}")

        # 將 example 轉換成 LLMAugmenter 輸入格式
        # 使用 ocr_text 作為來源
        augmenter_input = LLMAugmenterInput(
            source={"ocr_result": example['ocr_result']}
        )

        # 呼叫 augmenter 生成問題
        augment_output = augmenter.augment(augmenter_input)

        # 組合 Benchmark 結果 (使用 AutoGenOutput)
        result = AutoGenOutput(
            source_path=example['image_url'],
            ocr_text=example['ocr_result'],
            questions=augment_output.augmented_queries,
        )
        results.append(result.to_dict())

        # 組合原始回應資料
        raw_output = AutoGenRawOutput(
            source_path=example['image_url'],
            mode=mode,
            model_name=payload.get('model_name', ''),
            ocr_text=example['ocr_result'],
            raw_response=augment_output.raw_response
        )
        raw_outputs.append(raw_output.to_dict())

        # 輸出前 3 筆結果
        if idx <= 3:
            print(f"\n--- 第 {idx} 筆結果 ---")
            print(f"來源路徑：{result.source_path}")
            print(f"OCR 文本（前 1000 字）：{result.ocr_text[:1000]}...")
            print(f"生成問題數量：{len(result.questions)}")
            print(f"生成的問題：")
            for j, question in enumerate(result.questions, 1):
                print(f"  {j}. {question}")

    # 5. 儲存結果
    print(f"\n儲存結果...")
    save_benchmark(output_path, results)

    # 6. 儲存原始回應資料
    raw_output_path = output_path.replace('.json', '_raw_responses.json')
    save_raw_responses(raw_output_path, raw_outputs)

    print(f"\n✓ 完成！")


if __name__ == "__main__":
    gen_ques()
