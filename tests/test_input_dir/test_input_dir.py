#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試運行腳本
依次運行 test_excel, test_pdf, test_png, test_mix 配置
執行實際的 Pipeline 並產生結果
"""

import sys
import time
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 導入 main.py 中的執行函數
from core.main import (
    load_config,
    determine_pipeline_type,
    run_excel_pipeline,
    run_image_pipeline,
    run_pdf_pipeline
)


def run_pipeline_from_config(config_path: Path):
    """
    載入配置文件並執行對應的 Pipeline

    Args:
        config_path: 配置文件路徑

    Returns:
        執行結果字典: {"success": bool, "pipeline_type": str, "error": str (if failed), "elapsed_time": float}
    """
    start_time = time.time()

    print("\n" + "=" * 80)
    print(f"測試配置: {config_path.name}")
    print("=" * 80)

    if not config_path.exists():
        print(f"❌ 配置文件不存在: {config_path}")
        elapsed_time = time.time() - start_time
        return {"success": False, "error": "配置文件不存在", "elapsed_time": elapsed_time}

    try:
        # 載入配置
        config = load_config(config_path)
        print(f"✓ 配置文件載入成功")

        # 驗證基本結構
        if 'input' not in config:
            print(f"❌ 缺少 input 欄位")
            elapsed_time = time.time() - start_time
            return {"success": False, "error": "缺少 input 欄位", "elapsed_time": elapsed_time}

        # 判斷 Pipeline 類型
        try:
            pipeline_type = determine_pipeline_type(config)
            print(f"  Pipeline 類型: {pipeline_type}")
        except ValueError as e:
            print(f"❌ 無法判斷 Pipeline 類型: {e}")
            elapsed_time = time.time() - start_time
            return {"success": False, "error": str(e), "elapsed_time": elapsed_time}

        # 顯示輸入路徑
        input_path = Path(config['input'])
        print(f"  輸入路徑: {config['input']}")

        if not input_path.exists():
            print(f"  ❌ 輸入路徑不存在")
            elapsed_time = time.time() - start_time
            return {"success": False, "error": "輸入路徑不存在", "elapsed_time": elapsed_time}

        # 顯示元數據
        if 'metadata' in config:
            print(f"  元數據: {config['metadata']}")

        print("\n" + "-" * 80)
        print("開始執行 Pipeline...")
        print("-" * 80)

        # 根據 Pipeline 類型執行對應的處理
        if pipeline_type == 'excel':
            result = run_excel_pipeline(config)

            elapsed_time = time.time() - start_time

            if result.get("success"):
                print(f"\n✓ Excel Pipeline 執行成功")
                print(f"  - 處理模式: {'批次處理' if result.get('batch_mode') else '單檔處理'}")
                if result.get('batch_mode'):
                    print(f"  - 處理檔案數: {result.get('file_count', 'N/A')}")
                print(f"  - 處理數據數: {result.get('total_count', 'N/A')}")
                print(f"  - Parser 輸出: {result.get('parsed_data_path', 'N/A')}")
                print(f"  - Augmenter 輸出: {result.get('augmented_queries_path', 'N/A')}")
                print(f"  - 執行時間: {elapsed_time:.2f} 秒")

                return {
                    "success": True,
                    "pipeline_type": pipeline_type,
                    "result": result,
                    "elapsed_time": elapsed_time
                }
            else:
                error_msg = result.get('error', '未知錯誤')
                print(f"\n✗ 執行失敗: {error_msg}")
                print(f"  - 執行時間: {elapsed_time:.2f} 秒")
                return {"success": False, "pipeline_type": pipeline_type, "error": error_msg, "elapsed_time": elapsed_time}

        elif pipeline_type == 'image':
            success = run_image_pipeline(config)
            elapsed_time = time.time() - start_time

            if success:
                print(f"\n✓ Image Pipeline 執行成功")
                print(f"  - 執行時間: {elapsed_time:.2f} 秒")
                return {
                    "success": True,
                    "pipeline_type": pipeline_type,
                    "elapsed_time": elapsed_time
                }
            else:
                print(f"\n✗ Image Pipeline 執行失敗")
                print(f"  - 執行時間: {elapsed_time:.2f} 秒")
                return {"success": False, "pipeline_type": pipeline_type, "error": "執行失敗", "elapsed_time": elapsed_time}

        elif pipeline_type == 'pdf':
            success = run_pdf_pipeline(config)
            elapsed_time = time.time() - start_time

            if success:
                print(f"\n✓ PDF Pipeline 執行成功")
                print(f"  - 執行時間: {elapsed_time:.2f} 秒")
                return {
                    "success": True,
                    "pipeline_type": pipeline_type,
                    "elapsed_time": elapsed_time
                }
            else:
                print(f"\n✗ PDF Pipeline 執行失敗")
                print(f"  - 執行時間: {elapsed_time:.2f} 秒")
                return {"success": False, "pipeline_type": pipeline_type, "error": "執行失敗", "elapsed_time": elapsed_time}

        else:
            error_msg = f"不支援的 Pipeline 類型: {pipeline_type}"
            print(f"❌ {error_msg}")
            elapsed_time = time.time() - start_time
            return {"success": False, "error": error_msg, "elapsed_time": elapsed_time}

    except Exception as e:
        print(f"\n❌ 執行過程中發生異常")
        print(f"  {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        elapsed_time = time.time() - start_time
        print(f"  - 執行時間: {elapsed_time:.2f} 秒")
        return {"success": False, "error": f"{type(e).__name__}: {e}", "elapsed_time": elapsed_time}


def main():
    """主函數：依次執行所有測試配置"""
    # 從專案根目錄尋找 config
    script_dir = Path(__file__).parent
    configs_dir = script_dir / "config"

    # 要測試的配置文件列表
    test_configs = [
        "test_excel.yml",
        "test_pdf.yml",
        "test_png.yml",
        "test_mix.yml"
    ]

    print("\n" + "=" * 80)
    print("測試 Pipeline 執行")
    print("=" * 80)
    print("說明：依次執行 test_excel, test_pdf, test_png, test_mix 配置")
    print("=" * 80)

    results = {}

    for config_name in test_configs:
        config_path = configs_dir / config_name
        result = run_pipeline_from_config(config_path)
        results[config_name] = result
        print("-"*160)

    # 總結
    print("\n" + "=" * 80)
    print("測試總結")
    print("=" * 80)

    for config_name, result in results.items():
        success = result.get("success", False)
        status = "✓ 通過" if success else "❌ 失敗"
        pipeline_type = result.get("pipeline_type", "unknown")
        elapsed_time = result.get("elapsed_time", 0)

        print(f"{config_name}: {status} (Pipeline: {pipeline_type}, 時間: {elapsed_time:.2f}秒)")

        if not success and "error" in result:
            print(f"  錯誤: {result['error']}")

    total = len(results)
    passed = sum(1 for r in results.values() if r.get("success", False))
    total_time = sum(r.get("elapsed_time", 0) for r in results.values())

    print()
    print(f"總計: {passed}/{total} 個測試通過")
    print(f"總執行時間: {total_time:.2f} 秒")
    print("=" * 80)

    if all(r.get("success", False) for r in results.values()):
        print()
        print("✓ 所有測試都執行成功！")
        print()

    return 0 if all(r.get("success", False) for r in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
