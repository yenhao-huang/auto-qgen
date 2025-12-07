import sys
from pathlib import Path

# 將專案根目錄加入 Python 路徑
# 從 core/ 向上一層到達專案根目錄
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import json
import argparse
import yaml

from lib.ocr.paddleocr_vl import PaddleOCR
from lib.ocr.dotsocr import DotsOCR
from lib.ocr.chandra import ChandraOCR
from lib.ocr.nv_nemotron import NVNemotronOCR
from lib.ocr.base_ocr import BaseOCR
from schemas.schema import OCRLLMPayload

# 可用的 OCR 引擎映射
OCR_ENGINES = {
    "paddle": PaddleOCR,
    "paddleocr": PaddleOCR,
    "dots": DotsOCR,
    "dotsocr": DotsOCR,
    "chandra": ChandraOCR,
    "chandraocr": ChandraOCR,
    "nv_nemotron": NVNemotronOCR, 
}

def ocr(config_path: str = None):
    """主程式入口：從 YAML 配置檔讀取參數並執行 OCR

    Args:
        config_path: 配置檔路徑，如果為 None 則從命令列參數讀取
    """
    # 如果沒有提供 config_path，則從命令列參數讀取
    if config_path is None:
        parser = argparse.ArgumentParser(
            description="使用多種 OCR 引擎對圖片執行 OCR 辨識",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
範例：
    # 使用預設配置檔
    python core/ocr.py

    # 使用自訂配置檔
    python core/ocr.py --config configs/my_ocr_config.yml
        """
        )

        parser.add_argument(
            "--config",
            type=str,
            default="configs/ocr_config.yml",
            help="配置檔路徑（預設：configs/ocr_config.yml）"
        )

        args = parser.parse_args()
        config_path = args.config

    # 讀取 YAML 配置檔
    config_path = Path(config_path)
    if not config_path.exists():
        print(f"錯誤：配置檔不存在：{config_path}")
        return

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 從配置檔提取參數
    input_dir = config.get('input_dir')
    output_dir = config.get('output_dir')
    engine = config.get('engine', 'paddle')
    mode = config.get('mode', 'local')
    # 根據模式讀取對應的配置
    if mode == "vllm":
        vllm_config = config.get(mode, {})
        base_url = vllm_config.get('url', 'http://192.168.1.79:8074/v1')
        model = vllm_config.get('model_name', '/workspace/llm_model')
        temperature = vllm_config.get('temperature', 0.0)
        timeout = vllm_config.get('timeout', 3600)
        max_tokens = vllm_config.get('max_tokens', 18000)
        frequency_penalty = vllm_config.get('frequency_penalty', 0.1)
        presence_penalty = vllm_config.get('presence_penalty', 0.1)
        top_p = vllm_config.get('top_p', 0.9)
    elif mode == "openrouter":
        openrouter_config = config.get(mode, {})
        base_url = openrouter_config.get('url', 'https://openrouter.ai/api/v1/chat/completions')
        model = openrouter_config.get('model_name', 'anthropic/claude-3.5-sonnet')
        temperature = openrouter_config.get('temperature', 0.0)
        timeout = openrouter_config.get('timeout', 3600)
        max_tokens = openrouter_config.get('max_tokens', 18000)
        frequency_penalty = openrouter_config.get('frequency_penalty', 0.1)
        presence_penalty = openrouter_config.get('presence_penalty', 0.1)
        top_p = openrouter_config.get('top_p', 0.9)
    elif mode == "local":
        local_config = config.get(mode, {})
        base_url = local_config.get('url', 'http://localhost:8000')
        model = local_config.get('model_name', 'local_model')
        temperature = local_config.get('temperature', 0.0)
        timeout = local_config.get('timeout', 3600)
        max_tokens = local_config.get('max_tokens', 18000)
        frequency_penalty = local_config.get('frequency_penalty', 0.1)
        presence_penalty = local_config.get('presence_penalty', 0.1)
        top_p = local_config.get('top_p', 0.9)
    else:
        print(f"錯誤：不支援的模式：{mode}")
        print("可用模式：local, vllm, openrouter")
        return

    recursive = config.get('recursive', True)

    # 驗證必要參數
    if not input_dir:
        print("錯誤：配置檔中缺少 'input_dir' 參數")
        return
    if not output_dir:
        print("錯誤：配置檔中缺少 'output_dir' 參數")
        return

    # 驗證引擎選項
    if engine not in OCR_ENGINES:
        print(f"錯誤：無效的引擎選項：{engine}")
        print(f"可用選項：{', '.join(OCR_ENGINES.keys())}")
        return

    # 根據選擇的引擎取得對應的 OCR 類別
    ocr_class = OCR_ENGINES[engine]

    # 建立 LLM Payload 物件
    llm_payload = OCRLLMPayload(
        base_url=base_url,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty,
        timeout=timeout
    )

    # 初始化 OCR 處理器
    print(f"初始化 {ocr_class.__name__}...")
    print(f"  - 配置檔：{config_path}")
    print(f"  - OCR 引擎：{engine}")
    print(f"  - 模式：{mode}")
    print(f"  - 輸入目錄：{input_dir}")
    print(f"  - 輸出目錄：{output_dir}")
    print(f"  - 伺服器 URL：{base_url}")

    ocr: BaseOCR = ocr_class(
        llm_payload=llm_payload,
        output_dir=output_dir,
        mode=mode
    )

    # 執行批次 OCR
    print(f"\n開始處理圖片...")
    if recursive:
        print(f"  - 遞迴模式：啟用（將搜尋所有子目錄）")
    else:
        print(f"  - 遞迴模式：停用（只搜尋當前目錄）")

    batch_result = ocr.batch_ocr(input_dir, recursive=recursive)
    print(f"\n處理完成！")
    print(f"  - 總圖片數：{batch_result.total_images}")
    print(f"  - 成功：{batch_result.success}")
    print(f"  - 失敗：{batch_result.failed}")
    if batch_result.output_file:
        print(f"  - 結果已保存到：{batch_result.output_file}")

    return batch_result

if __name__ == "__main__":
    batch_result = ocr()