#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡單測試執行器（不需要 pytest）
用於快速驗證測試文件的基本功能
"""

import sys
from pathlib import Path

# 將專案根目錄加入 Python 路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import argparse
from core.main import load_config, get_file_type, determine_pipeline_type


def test_excel_file():
    """測試 Excel 文件"""
    print("\n" + "=" * 80)
    print("測試 Excel 文件類型")
    print("=" * 80)

    excel_file = project_root / "tests/testcases/filetypes/表7-3-2.xlsx"

    # 測試文件存在
    print(f"✓ 測試文件路徑: {excel_file}")
    assert excel_file.exists(), f"測試文件不存在: {excel_file}"
    print(f"✓ 文件存在檢查通過")

    # 測試文件類型檢測
    file_type = get_file_type(excel_file)
    print(f"✓ 檢測到的文件類型: {file_type}")
    assert file_type == 'excel', f"應檢測為 excel，實際為 {file_type}"
    print(f"✓ 文件類型檢測通過")

    # 測試自動檢測 Pipeline 類型
    config = {
        'pipeline_type': 'auto',
        'input': str(excel_file)
    }
    pipeline_type = determine_pipeline_type(config)
    print(f"✓ 自動檢測的 Pipeline 類型: {pipeline_type}")
    assert pipeline_type == 'excel', f"應自動檢測為 excel，實際為 {pipeline_type}"
    print(f"✓ Pipeline 類型自動檢測通過")

    print("\n✓ Excel 文件測試全部通過！")
    return True


def test_image_file():
    """測試圖片文件"""
    print("\n" + "=" * 80)
    print("測試圖片文件類型")
    print("=" * 80)

    image_file = project_root / "tests/testcases/filetypes/(檔案下載)113年度長期照顧服務機構評鑑結果-第一批次名單_page_0002.png"

    # 測試文件存在
    print(f"✓ 測試文件路徑: {image_file}")
    assert image_file.exists(), f"測試文件不存在: {image_file}"
    print(f"✓ 文件存在檢查通過")

    # 測試文件類型檢測
    file_type = get_file_type(image_file)
    print(f"✓ 檢測到的文件類型: {file_type}")
    assert file_type == 'image', f"應檢測為 image，實際為 {file_type}"
    print(f"✓ 文件類型檢測通過")

    # 測試自動檢測 Pipeline 類型
    config = {
        'pipeline_type': 'auto',
        'input': str(image_file)
    }
    pipeline_type = determine_pipeline_type(config)
    print(f"✓ 自動檢測的 Pipeline 類型: {pipeline_type}")
    assert pipeline_type == 'image', f"應自動檢測為 image，實際為 {pipeline_type}"
    print(f"✓ Pipeline 類型自動檢測通過")

    print("\n✓ 圖片文件測試全部通過！")
    return True


def test_pdf_file():
    """測試 PDF 文件"""
    print("\n" + "=" * 80)
    print("測試 PDF 文件類型")
    print("=" * 80)

    pdf_file = project_root / "tests/testcases/filetypes/(公告)109年度獎助布建住宿式長照機構公共化資源計畫.pdf"

    # 測試文件存在
    print(f"✓ 測試文件路徑: {pdf_file}")
    assert pdf_file.exists(), f"測試文件不存在: {pdf_file}"
    print(f"✓ 文件存在檢查通過")

    # 測試文件類型檢測
    file_type = get_file_type(pdf_file)
    print(f"✓ 檢測到的文件類型: {file_type}")
    assert file_type == 'pdf', f"應檢測為 pdf，實際為 {file_type}"
    print(f"✓ 文件類型檢測通過")

    # 測試自動檢測 Pipeline 類型
    config = {
        'pipeline_type': 'auto',
        'input': str(pdf_file)
    }
    pipeline_type = determine_pipeline_type(config)
    print(f"✓ 自動檢測的 Pipeline 類型: {pipeline_type}")
    assert pipeline_type == 'pdf', f"應自動檢測為 pdf，實際為 {pipeline_type}"
    print(f"✓ Pipeline 類型自動檢測通過")

    print("\n✓ PDF 文件測試全部通過！")
    return True


def test_config_file():
    """測試配置文件載入"""
    print("\n" + "=" * 80)
    print("測試配置文件載入")
    print("=" * 80)

    config_file = project_root / "configs/unified_pipeline.example.yml"

    if not config_file.exists():
        print(f"⊘ 配置文件不存在，跳過測試: {config_file}")
        return True

    # 測試配置文件載入
    print(f"✓ 配置文件路徑: {config_file}")
    config = load_config(config_file)
    print(f"✓ 配置文件載入成功")

    # 檢查基本結構
    assert isinstance(config, dict), "配置應為字典類型"
    print(f"✓ 配置結構檢查通過")

    # 檢查關鍵欄位
    if 'pipeline_type' in config:
        print(f"✓ 找到 pipeline_type: {config['pipeline_type']}")
    if 'input' in config:
        print(f"✓ 找到 input: {config['input']}")

    print("\n✓ 配置文件測試全部通過！")
    return True


def main():
    """主程式入口"""
    parser = argparse.ArgumentParser(
        description="簡單測試執行器 - 不需要 pytest",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例：
    # 執行所有測試
    python tests/test_filetype/simple_runner.py

    # 只執行 Excel 測試
    python tests/test_filetype/simple_runner.py --excel

    # 只執行 Image 測試
    python tests/test_filetype/simple_runner.py --image

    # 只執行 PDF 測試
    python tests/test_filetype/simple_runner.py --pdf

    # 只執行配置文件測試
    python tests/test_filetype/simple_runner.py --config
        """
    )

    parser.add_argument(
        '--excel',
        action='store_true',
        help='只執行 Excel 測試'
    )

    parser.add_argument(
        '--image',
        action='store_true',
        help='只執行 Image 測試'
    )

    parser.add_argument(
        '--pdf',
        action='store_true',
        help='只執行 PDF 測試'
    )

    parser.add_argument(
        '--config',
        action='store_true',
        help='只執行配置文件測試'
    )

    args = parser.parse_args()

    print("=" * 80)
    print("文件類型簡單測試執行器")
    print("=" * 80)
    print(f"專案根目錄: {project_root}")
    print("=" * 80)

    results = []

    try:
        # 根據參數執行對應的測試
        if args.excel:
            results.append(('Excel', test_excel_file()))
        elif args.image:
            results.append(('Image', test_image_file()))
        elif args.pdf:
            results.append(('PDF', test_pdf_file()))
        elif args.config:
            results.append(('Config', test_config_file()))
        else:
            # 執行所有測試
            results.append(('Excel', test_excel_file()))
            results.append(('Image', test_image_file()))
            results.append(('PDF', test_pdf_file()))
            results.append(('Config', test_config_file()))

        # 顯示摘要
        print("\n" + "=" * 80)
        print("測試摘要")
        print("=" * 80)

        all_passed = True
        for name, passed in results:
            status = "✓ 通過" if passed else "✗ 失敗"
            print(f"{name:15s}: {status}")
            if not passed:
                all_passed = False

        print("=" * 80)

        if all_passed:
            print("\n✓ 所有測試通過！")
            sys.exit(0)
        else:
            print("\n✗ 部分測試失敗")
            sys.exit(1)

    except AssertionError as e:
        print(f"\n✗ 測試失敗: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ 發生錯誤: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
