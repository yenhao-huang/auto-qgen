#!/usr/bin/env python3
"""
主執行腳本
整合 OCR 和生成問題功能
"""
import sys
from pathlib import Path

# 將專案根目錄加入 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import argparse
from core.ocr import ocr
from core.gen_ques_for_img import gen_ques


def main():
    """主程式入口：執行 OCR 後自動生成問題"""
    parser = argparse.ArgumentParser(
        description="執行 OCR 辨識並生成問題",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例：
    # 使用預設配置檔
    python core/run.py

    # 使用自訂配置檔
    python core/run.py --ocr-config configs/my_ocr_config.yml --gen-ques-config configs/my_gen_ques_config.yml

    # 只執行 OCR
    python core/run.py --ocr-only --ocr-config configs/my_ocr_config.yml

    # 只執行生成問題
    python core/run.py --gen-ques-only --gen-ques-config configs/my_gen_ques_config.yml
        """
    )

    parser.add_argument(
        "--ocr-config",
        type=str,
        default="configs/ocr_config.yml",
        help="OCR 配置檔路徑（預設：configs/ocr_config.yml）"
    )

    parser.add_argument(
        "--gen-ques-config",
        type=str,
        default="configs/gen_ques_config.yml",
        help="生成問題配置檔路徑（預設：configs/gen_ques_config.yml）"
    )

    parser.add_argument(
        "--ocr-only",
        action="store_true",
        help="只執行 OCR，不執行生成問題"
    )

    parser.add_argument(
        "--gen-ques-only",
        action="store_true",
        help="只執行生成問題，不執行 OCR"
    )

    args = parser.parse_args()

    # 檢查互斥選項
    if args.ocr_only and args.gen_ques_only:
        print("錯誤：--ocr-only 和 --gen-ques-only 不能同時使用")
        return

    print("=" * 80)
    print("開始執行流程")
    print("=" * 80)

    # 執行 OCR
    if not args.gen_ques_only:
        print("\n" + "=" * 80)
        print("步驟 1: 執行 OCR 辨識")
        print("=" * 80)
        batch_result = ocr(config_path=args.ocr_config)

        if not batch_result:
            print("\n錯誤：OCR 執行失敗")
            return

        print(f"\n✓ OCR 完成")
        print(f"  - 總圖片數：{batch_result.total_images}")
        print(f"  - 成功：{batch_result.success}")
        print(f"  - 失敗：{batch_result.failed}")

    # 執行生成問題
    if not args.ocr_only:
        print("\n" + "=" * 80)
        print("步驟 2: 生成問題")
        print("=" * 80)
        gen_ques(config_path=args.gen_ques_config)

        print(f"\n✓ 生成問題完成")

    print("\n" + "=" * 80)
    print("全部流程執行完成！")
    print("=" * 80)


if __name__ == "__main__":
    main()
