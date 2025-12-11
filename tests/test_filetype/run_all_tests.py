#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
統一測試執行器
執行所有文件類型的測試（Excel, Image, PDF）
"""

import sys
from pathlib import Path

# 將專案根目錄加入 Python 路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
import argparse
from typing import List, Optional


def run_all_tests(
    verbose: bool = False,
    markers: Optional[str] = None,
    test_files: Optional[List[str]] = None
) -> int:
    """
    執行所有測試

    Args:
        verbose: 是否顯示詳細輸出
        markers: pytest markers 過濾器（例如：'not skip'）
        test_files: 指定要執行的測試文件列表

    Returns:
        退出碼（0 表示成功，非 0 表示失敗）
    """
    test_dir = Path(__file__).parent

    # 構建 pytest 參數
    pytest_args = [str(test_dir)]

    # 詳細輸出
    if verbose:
        pytest_args.append('-v')
    else:
        pytest_args.append('-q')

    # 顯示測試摘要
    pytest_args.append('--tb=short')

    # 顯示所有輸出
    if verbose:
        pytest_args.append('-s')

    # 使用 markers 過濾
    if markers:
        pytest_args.extend(['-m', markers])

    # 指定測試文件
    if test_files:
        pytest_args = []
        for test_file in test_files:
            test_path = test_dir / test_file
            if test_path.exists():
                pytest_args.append(str(test_path))
            else:
                print(f"警告：測試文件不存在 - {test_file}")

        if not pytest_args:
            print("錯誤：沒有找到有效的測試文件")
            return 1

        if verbose:
            pytest_args.extend(['-v', '-s'])
        else:
            pytest_args.append('-q')

        pytest_args.append('--tb=short')

    print("=" * 80)
    print("執行文件類型測試")
    print("=" * 80)
    print(f"測試目錄: {test_dir}")
    print(f"pytest 參數: {' '.join(pytest_args)}")
    print("=" * 80)

    # 執行測試
    exit_code = pytest.main(pytest_args)

    return exit_code


def run_excel_tests(verbose: bool = False) -> int:
    """執行 Excel 測試"""
    return run_all_tests(verbose=verbose, test_files=['test_excel.py'])


def run_image_tests(verbose: bool = False) -> int:
    """執行 Image 測試"""
    return run_all_tests(verbose=verbose, test_files=['test_image.py'])


def run_pdf_tests(verbose: bool = False) -> int:
    """執行 PDF 測試"""
    return run_all_tests(verbose=verbose, test_files=['test_pdf.py'])


def run_basic_tests(verbose: bool = False) -> int:
    """執行基本測試（不包含需要服務運行的測試）"""
    return run_all_tests(verbose=verbose, markers='not skip')


def main():
    """主程式入口"""
    parser = argparse.ArgumentParser(
        description="統一測試執行器 - 執行文件類型測試",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例：
    # 執行所有測試
    python tests/test_filetype/run_all_tests.py

    # 執行所有測試（詳細輸出）
    python tests/test_filetype/run_all_tests.py -v

    # 只執行 Excel 測試
    python tests/test_filetype/run_all_tests.py --excel

    # 只執行 Image 測試
    python tests/test_filetype/run_all_tests.py --image

    # 只執行 PDF 測試
    python tests/test_filetype/run_all_tests.py --pdf

    # 執行基本測試（不包含需要服務的測試）
    python tests/test_filetype/run_all_tests.py --basic

    # 使用自訂 markers
    python tests/test_filetype/run_all_tests.py -m "not skip"
        """
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='顯示詳細輸出'
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
        '--basic',
        action='store_true',
        help='只執行基本測試（不包含需要服務的測試）'
    )

    parser.add_argument(
        '-m', '--markers',
        type=str,
        help='pytest markers 過濾器（例如："not skip"）'
    )

    args = parser.parse_args()

    # 根據參數執行對應的測試
    if args.excel:
        exit_code = run_excel_tests(verbose=args.verbose)
    elif args.image:
        exit_code = run_image_tests(verbose=args.verbose)
    elif args.pdf:
        exit_code = run_pdf_tests(verbose=args.verbose)
    elif args.basic:
        exit_code = run_basic_tests(verbose=args.verbose)
    else:
        # 執行所有測試
        exit_code = run_all_tests(verbose=args.verbose, markers=args.markers)

    # 顯示結果
    print("\n" + "=" * 80)
    if exit_code == 0:
        print("✓ 所有測試通過")
    else:
        print("✗ 部分測試失敗")
    print("=" * 80)

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
