#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Augment Service - 將 Excel 解析與增強查詢封裝為服務類別
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import yaml
from tqdm import tqdm

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.parser.excel_parser_llm import ExcelParserLLM
from utils.augmenter.llm_augmenter import LLMAugmenter
from utils.schemas import GroundTruth, AugmenterInput


class AugmentService:
    """
    Excel 數據增強服務類別
    將 Excel 文件解析並生成增強查詢的完整流程封裝為類別
    """

    def __init__(self, config: Dict[str, Any], quiet: bool = True):
        """
        初始化服務

        Args:
            config: 配置字典，包含 parser、augmenter、input、output 等設定
            quiet: 是否靜默模式（不顯示進度條和詳細訊息）
        """
        self.config = config
        self.quiet = quiet
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 初始化 Parser LLM
        self.parser_llm = ExcelParserLLM(
            vllm_url=config['parser']['llm']['url'],
            model=config['parser']['llm']['model'],
            api_key=config['parser']['llm']['api_key'],
            use_openrouter=config['parser']['llm']['use_openrouter'],
            max_retries=config['parser']['llm']['max_retries']
        )

        # 初始化 Augmenter LLM
        self.augmenter_llm = LLMAugmenter(
            vllm_url=config['augmenter']['llm']['url'],
            model=config['augmenter']['llm']['model'],
            prompt_name=config['augmenter']['prompt_name'],
            api_key=config['augmenter']['llm']['api_key'],
            use_openrouter=config['augmenter']['llm']['use_openrouter']
        )

    @staticmethod
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

    def run(self,
            input_file: Path,
            output_dir: Path = None,
            skip_parser: bool = False,
            parsed_data_path: Path = None) -> Dict[str, Any]:
        """
        執行完整的數據增強流程

        Args:
            input_file: 輸入的 Excel 檔案路徑
            output_dir: 輸出目錄（可選，預設使用 timestamp 目錄）
            skip_parser: 是否跳過 Parser 步驟
            parsed_data_path: 已解析的數據路徑（當 skip_parser=True 時使用）

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
            # 設定輸出目錄
            if output_dir is None:
                output_dir = Path(f"results/pipeline_{self.timestamp}")
            output_dir.mkdir(parents=True, exist_ok=True)

            # 設定各階段輸出路徑
            parsed_output_path = output_dir / "parsed_data.json"
            augmenter_output_path = output_dir / "augmented_queries.json"

            if not self.quiet:
                print("=" * 70)
                print("Excel Parser LLM + Augmenter Service")
                print("=" * 70)
                print(f"輸入檔案: {input_file}")
                print(f"輸出目錄: {output_dir}")
                print("=" * 70)

            # ==================== 步驟 1: Parser ====================
            if skip_parser:
                if not self.quiet:
                    print("\n跳過 Parser 步驟，從已解析的檔案讀取...")

                if parsed_data_path is None or not parsed_data_path.exists():
                    raise FileNotFoundError(f"找不到已解析的檔案 - {parsed_data_path}")

                with open(parsed_data_path, 'r', encoding='utf-8') as f:
                    result = json.load(f)

                if not self.quiet:
                    print(f"  已載入 {len(result.get('cells', []))} 個儲存格")
            else:
                # 驗證輸入檔案
                if not input_file.exists():
                    raise FileNotFoundError(f"輸入檔案不存在 - {input_file}")

                if not self.quiet:
                    print("\n步驟 1/2: 使用 LLM 解析 Excel 檔案")
                    print("-" * 70)

                result = self.parser_llm.parse_excel_with_llm(input_file)
                self.parser_llm.save_result(result, parsed_output_path)

                if not self.quiet:
                    print(f"\n解析結果摘要：")
                    print(f"  標題: {result.get('title', 'N/A')}")
                    print(f"  X 軸: {result.get('x-axis', 'N/A')}")
                    print(f"  Y 軸: {result.get('y-axis', 'N/A')}")
                    print(f"  重要儲存格數: {len(result.get('cells', []))}")

            # ==================== 轉換格式 ====================
            if not self.quiet:
                print("\n轉換為 AugmenterInput 格式...")

            inputs = ExcelParserLLM.transform_to_augmenterInput(result)

            if not self.quiet:
                print(f"  已轉換 {len(inputs)} 個儲存格")

            # ==================== 步驟 2: Augmenter ====================
            if not self.quiet:
                print("\n步驟 2/2: 使用 LLM 生成增強查詢")
                print("-" * 70)

            results = []
            for idx, item in enumerate(tqdm(inputs, desc="生成查詢", disable=self.quiet)):
                try:
                    # 共同欄位 ground_truth（必要）
                    gt_raw = item["ground_truth"]
                    ground_truth = GroundTruth(
                        file_name=gt_raw["file_name"],
                        item_id=gt_raw["item_id"],
                    )

                    if "keyword" not in item or not isinstance(item["keyword"], dict):
                        if not self.quiet:
                            print(f"警告：第 {idx} 筆 keyword 模式需要 'keyword'（dict）欄位", file=sys.stderr)
                        continue

                    aug_in = AugmenterInput(
                        keyword=item["keyword"],
                        ground_truth=ground_truth,
                        metadata=item.get("metadata", {})
                    )
                    results.append(self.augmenter_llm.augment(aug_in))

                except KeyError as e:
                    if not self.quiet:
                        print(f"警告：第 {idx} 筆資料缺少必要欄位：{e}", file=sys.stderr)
                    continue
                except Exception as e:
                    if not self.quiet:
                        print(f"警告：第 {idx} 筆資料處理失敗：{e}", file=sys.stderr)
                    continue

            # 儲存結果 (使用絕對路徑)
            self.augmenter_llm.save_augment_results(results, str(augmenter_output_path.resolve()))

            # ==================== 完成 ====================
            if not self.quiet:
                print("\n" + "=" * 70)
                print("處理完成！")
                print("=" * 70)
                print(f"總共處理: {len(results)} 筆資料")
                print(f"\n輸出檔案:")
                print(f"  1. Parser 輸出: {parsed_output_path}")
                print(f"  2. Augmenter 輸出: {augmenter_output_path}")
                print("=" * 70)

            return {
                "success": True,
                "parsed_data_path": str(parsed_output_path.resolve()),
                "augmented_queries_path": str(augmenter_output_path.resolve()),
                "augmented_queries": results,
                "total_count": len(results)
            }

        except Exception as e:
            error_msg = f"處理失敗: {str(e)}"
            if not self.quiet:
                print(f"\n錯誤：{error_msg}", file=sys.stderr)
                import traceback
                traceback.print_exc()

            return {
                "success": False,
                "error": error_msg,
                "total_count": 0
            }
