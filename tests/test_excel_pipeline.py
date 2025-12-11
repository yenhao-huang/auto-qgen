#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel Pipeline 完整測試
測試 testcase/excel 目錄下的多個 Excel 文件
包含：Excel Parser、Transform、Augmenter 的完整流程測試
"""

import sys
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List

# 嘗試導入 pytest，如果沒有則使用替代方案
try:
    import pytest
    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False
    # 提供 pytest 的基本替代
    class pytest:
        @staticmethod
        def skip(msg):
            print(f"⊘ 跳過測試: {msg}")
            return

        class fixture:
            def __init__(self, *args, **kwargs):
                pass

            def __call__(self, func):
                return func

# 將專案根目錄加入 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.excel_pipeline import excel_parse, augment, run, load_config
from lib.parser.excel_parser_llm import ExcelParserLLM
from schemas.schema import LLMAugmenterInput


class TestExcelParser:
    """測試 Excel Parser 功能"""

    @pytest.fixture
    def test_excel_files(self):
        """提供測試用的 Excel 文件列表"""
        test_dir = Path("tests/testcases/excel")
        if not test_dir.exists():
            pytest.skip(f"測試目錄不存在: {test_dir}")

        excel_files = list(test_dir.glob("*.xlsx"))
        if not excel_files:
            pytest.skip(f"在 {test_dir} 中找不到 Excel 文件")

        return excel_files

    @pytest.fixture
    def mock_config(self):
        """提供模擬的配置"""
        return {
            'parser': {
                'llm': {
                    'url': 'http://localhost:8074/v1/chat/completions',
                    'model': 'meta-llama/Llama-3.3-70B-Instruct',
                    'api_key': 'sk-test-key',
                    'use_openrouter': False,
                    'max_retries': 3
                }
            },
            'augmenter': {
                'mode': 'vllm',
                'prompt_name': 'default',
                'vllm': {
                    'url': 'http://localhost:8074/v1/chat/completions',
                    'model_name': 'meta-llama/Llama-3.3-70B-Instruct',
                    'max_tokens': 18000,
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'frequency_penalty': 0.1,
                    'presence_penalty': 0.1,
                    'is_thinking_mode': False,
                    'limit_llmoutput_scheme': False
                }
            },
            'input': {},
            'output': {},
            'verbose': False
        }

    def test_excel_parser_initialization(self):
        """測試 Excel Parser 初始化"""
        parser = ExcelParserLLM(
            vllm_url='http://localhost:8074/v1/chat/completions',
            model='test-model',
            api_key='test-key',
            use_openrouter=False,
            max_retries=3
        )

        assert parser.vllm_url == 'http://localhost:8074/v1/chat/completions'
        assert parser.model == 'test-model'
        assert parser.api_key == 'test-key'
        assert parser.use_openrouter is False
        assert parser.max_retries == 3
        print("✓ Excel Parser 初始化測試通過")

    def test_load_excel_single_file(self, test_excel_files):
        """測試載入單個 Excel 文件"""
        parser = ExcelParserLLM(
            vllm_url='http://localhost:8074/v1/chat/completions',
            model='test-model'
        )

        for excel_file in test_excel_files:
            print(f"\n測試文件: {excel_file.name}")

            # 載入 Excel
            excel_data = parser.load_excel(excel_file)

            # 驗證基本結構
            assert 'file_name' in excel_data
            assert 'sheet_name' in excel_data
            assert 'cells' in excel_data
            assert isinstance(excel_data['cells'], list)
            assert len(excel_data['cells']) > 0

            # 驗證儲存格資料
            first_cell = excel_data['cells'][0]
            assert 'row' in first_cell
            assert 'col' in first_cell
            assert 'address' in first_cell
            assert 'value' in first_cell

            print(f"  ✓ 文件名: {excel_data['file_name']}")
            print(f"  ✓ 工作表: {excel_data['sheet_name']}")
            print(f"  ✓ 儲存格數: {len(excel_data['cells'])}")
            print(f"  ✓ 第一個儲存格: {first_cell['address']} = {first_cell['value']}")

    def test_load_excel_batch(self):
        """測試批次載入多個 Excel 文件"""
        test_dir = Path("tests/testcases/excel")
        if not test_dir.exists():
            pytest.skip(f"測試目錄不存在: {test_dir}")

        excel_files = list(test_dir.glob("*.xlsx"))
        if len(excel_files) < 2:
            pytest.skip(f"測試文件不足（需要至少 2 個）")

        parser = ExcelParserLLM(
            vllm_url='http://localhost:8074/v1/chat/completions',
            model='test-model'
        )

        print(f"\n批次測試 {len(excel_files)} 個文件:")
        results = []

        for excel_file in excel_files:
            excel_data = parser.load_excel(excel_file)
            results.append({
                'file': excel_file.name,
                'cells_count': len(excel_data['cells']),
                'sheet': excel_data['sheet_name']
            })
            print(f"  ✓ {excel_file.name}: {len(excel_data['cells'])} 個儲存格")

        # 驗證所有文件都成功載入
        assert len(results) == len(excel_files)
        assert all(r['cells_count'] > 0 for r in results)

        print(f"\n✓ 批次載入測試通過，總共 {len(results)} 個文件")

    def test_column_name_conversion(self):
        """測試欄位名稱轉換"""
        parser = ExcelParserLLM(
            vllm_url='http://localhost:8074/v1/chat/completions',
            model='test-model'
        )

        # 測試基本轉換
        assert parser.get_column_name(1) == 'A'
        assert parser.get_column_name(26) == 'Z'
        assert parser.get_column_name(27) == 'AA'
        assert parser.get_column_name(52) == 'AZ'
        assert parser.get_column_name(53) == 'BA'
        assert parser.get_column_name(702) == 'ZZ'
        assert parser.get_column_name(703) == 'AAA'

        print("✓ 欄位名稱轉換測試通過")

    def test_transform_to_augmenter_input(self, test_excel_files):
        """測試轉換為 AugmenterInput 格式"""
        parser = ExcelParserLLM(
            vllm_url='http://localhost:8074/v1/chat/completions',
            model='test-model'
        )

        for excel_file in test_excel_files:
            print(f"\n測試轉換: {excel_file.name}")

            # 載入並解析 Excel（這裡我們模擬已解析的數據）
            excel_data = parser.load_excel(excel_file)

            # 構建模擬的解析結果
            # 為儲存格添加 LLM 解析後的欄位
            mock_cells = []
            for cell in excel_data['cells'][:5]:
                cell_with_analysis = cell.copy()
                cell_with_analysis['x-axis id 意思'] = f"X軸意義-{cell['address']}"
                cell_with_analysis['y-axis id 意思'] = f"Y軸意義-{cell['address']}"
                cell_with_analysis['值'] = cell['value']
                mock_cells.append(cell_with_analysis)

            mock_parsed_data = {
                'file_name': excel_data['file_name'],
                'sheet_name': excel_data['sheet_name'],
                'title': '測試標題',
                'x-axis': 'X軸說明',
                'y-axis': 'Y軸說明',
                'file_path': str(excel_file),
                'cells': mock_cells
            }

            # 轉換為 AugmenterInput
            augmenter_inputs = ExcelParserLLM.transform_to_augmenterInput(mock_parsed_data)

            # 驗證
            assert isinstance(augmenter_inputs, list)
            assert len(augmenter_inputs) > 0

            # 驗證每個 input 的結構
            for aug_input in augmenter_inputs:
                assert 'source' in aug_input
                assert 'source_path' in aug_input
                assert isinstance(aug_input['source'], dict)

                # 驗證 source 包含必要欄位
                source = aug_input['source']
                assert 'table_title' in source
                assert "table's x-axis" in source
                assert "table's y-axis" in source
                assert "cell's x-axis id 意思" in source
                assert "cell's y-axis id 意思" in source
                assert '值' in source

            print(f"  ✓ 轉換成功: {len(augmenter_inputs)} 個 AugmenterInput")
            print(f"  ✓ 第一個 source_path: {augmenter_inputs[0]['source_path']}")


class TestExcelPipeline:
    """測試完整的 Excel Pipeline"""

    @pytest.fixture
    def temp_output_dir(self):
        """提供臨時輸出目錄"""
        temp_dir = Path(tempfile.mkdtemp(prefix="test_excel_pipeline_"))
        yield temp_dir
        # 清理
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_config(self, temp_output_dir):
        """提供模擬的配置"""
        return {
            'parser': {
                'llm': {
                    'url': 'http://localhost:8074/v1/chat/completions',
                    'model': 'meta-llama/Llama-3.3-70B-Instruct',
                    'api_key': 'sk-test-key',
                    'use_openrouter': False,
                    'max_retries': 3
                }
            },
            'augmenter': {
                'mode': 'vllm',
                'prompt_name': 'default',
                'vllm': {
                    'url': 'http://localhost:8074/v1/chat/completions',
                    'model_name': 'meta-llama/Llama-3.3-70B-Instruct',
                    'max_tokens': 18000,
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'frequency_penalty': 0.1,
                    'presence_penalty': 0.1,
                    'is_thinking_mode': False,
                    'limit_llmoutput_scheme': False
                }
            },
            'input': {},
            'output': {
                'dir': str(temp_output_dir)
            },
            'verbose': False
        }

    def test_excel_parse_single_file_structure(self, mock_config):
        """測試單文件解析（僅測試結構，不實際調用 LLM）"""
        test_file = Path("tests/testcases/excel/表5-3.xlsx")
        if not test_file.exists():
            pytest.skip(f"測試文件不存在: {test_file}")

        # 更新配置
        mock_config['input']['file_path'] = str(test_file)
        mock_config['input']['skip_parser'] = True  # 跳過實際的 LLM 調用

        # 創建一個模擬的解析結果文件
        temp_parsed = Path(mock_config['output']['dir']) / "mock_parsed.json"
        temp_parsed.parent.mkdir(parents=True, exist_ok=True)

        # 載入真實的 Excel 結構
        parser = ExcelParserLLM(
            vllm_url='http://localhost:8074/v1/chat/completions',
            model='test-model'
        )
        excel_data = parser.load_excel(test_file)

        # 為儲存格添加 LLM 解析後的欄位
        mock_cells = []
        for cell in excel_data['cells'][:10]:
            cell_with_analysis = cell.copy()
            cell_with_analysis['x-axis id 意思'] = f"X軸意義-{cell['address']}"
            cell_with_analysis['y-axis id 意思'] = f"Y軸意義-{cell['address']}"
            cell_with_analysis['值'] = cell['value']
            mock_cells.append(cell_with_analysis)

        mock_result = {
            'file_name': excel_data['file_name'],
            'sheet_name': excel_data['sheet_name'],
            'title': '測試標題',
            'x-axis': 'X軸說明',
            'y-axis': 'Y軸說明',
            'file_path': str(test_file),
            'cells': mock_cells
        }

        with open(temp_parsed, 'w', encoding='utf-8') as f:
            json.dump(mock_result, f, ensure_ascii=False, indent=2)

        mock_config['input']['parsed_data_path'] = str(temp_parsed)

        # 執行解析
        result = excel_parse(mock_config)

        # 驗證結果
        assert result['success'] is True
        assert 'parsed_data' in result
        assert 'augmenter_inputs' in result
        assert 'total_count' in result
        assert result['total_count'] > 0

        print(f"\n✓ 單文件解析測試通過")
        print(f"  - 文件: {test_file.name}")
        print(f"  - 轉換數量: {result['total_count']}")

    def test_excel_parse_batch_mode_structure(self, mock_config):
        """測試批次模式解析（僅測試結構，不實際調用 LLM）"""
        test_dir = Path("tests/testcases/excel")
        if not test_dir.exists():
            pytest.skip(f"測試目錄不存在: {test_dir}")

        excel_files = list(test_dir.glob("*.xlsx"))
        if len(excel_files) < 2:
            pytest.skip(f"測試文件不足（需要至少 2 個）")

        # 更新配置為批次模式
        mock_config['input']['input_dir'] = str(test_dir)
        mock_config['input']['skip_parser'] = True

        # 創建模擬的批次解析結果
        parser = ExcelParserLLM(
            vllm_url='http://localhost:8074/v1/chat/completions',
            model='test-model'
        )

        # 合併所有文件的儲存格
        all_cells = []
        for excel_file in excel_files[:2]:  # 只測試前 2 個
            excel_data = parser.load_excel(excel_file)
            # 為每個儲存格添加來源文件資訊和 LLM 解析後的欄位
            for cell in excel_data['cells'][:5]:
                cell_with_analysis = cell.copy()
                cell_with_analysis['source_file'] = excel_data['file_name']
                cell_with_analysis['x-axis id 意思'] = f"X軸意義-{cell['address']}"
                cell_with_analysis['y-axis id 意思'] = f"Y軸意義-{cell['address']}"
                cell_with_analysis['值'] = cell['value']
                all_cells.append(cell_with_analysis)

        mock_batch_result = {
            'batch_mode': True,
            'files_processed': [f.name for f in excel_files[:2]],
            'title': '批次測試標題',
            'x-axis': 'X軸說明',
            'y-axis': 'Y軸說明',
            'file_path': str(test_dir),
            'cells': all_cells
        }

        temp_parsed = Path(mock_config['output']['dir']) / "batch_parsed.json"
        with open(temp_parsed, 'w', encoding='utf-8') as f:
            json.dump(mock_batch_result, f, ensure_ascii=False, indent=2)

        mock_config['input']['parsed_data_path'] = str(temp_parsed)

        # 執行批次解析
        result = excel_parse(mock_config)

        # 驗證結果
        assert result['success'] is True
        assert result['total_count'] > 0
        assert len(result['augmenter_inputs']) > 0

        print(f"\n✓ 批次模式解析測試通過")
        print(f"  - 文件數: {len(excel_files[:2])}")
        print(f"  - 總儲存格數: {result['total_count']}")

    def test_config_validation(self):
        """測試配置驗證"""
        # 測試缺少輸入的情況
        invalid_config = {
            'parser': {},
            'input': {},
            'output': {},
            'verbose': False
        }

        result = excel_parse(invalid_config)
        assert result['success'] is False
        assert 'error' in result
        print("\n✓ 配置驗證測試通過（正確拒絕無效配置）")

    def test_output_structure(self, mock_config):
        """測試輸出結構"""
        test_file = Path("tests/testcases/excel/表5-3.xlsx")
        if not test_file.exists():
            pytest.skip(f"測試文件不存在: {test_file}")

        mock_config['input']['file_path'] = str(test_file)
        mock_config['input']['skip_parser'] = True

        # 創建模擬數據
        parser = ExcelParserLLM(
            vllm_url='http://localhost:8074/v1/chat/completions',
            model='test-model'
        )
        excel_data = parser.load_excel(test_file)

        # 為儲存格添加 LLM 解析後的欄位
        mock_cells = []
        for cell in excel_data['cells'][:3]:
            cell_with_analysis = cell.copy()
            cell_with_analysis['x-axis id 意思'] = f"X軸意義-{cell['address']}"
            cell_with_analysis['y-axis id 意思'] = f"Y軸意義-{cell['address']}"
            cell_with_analysis['值'] = cell['value']
            mock_cells.append(cell_with_analysis)

        mock_result = {
            'file_name': excel_data['file_name'],
            'sheet_name': excel_data['sheet_name'],
            'title': '測試標題',
            'x-axis': 'X軸',
            'y-axis': 'Y軸',
            'file_path': str(test_file),
            'cells': mock_cells
        }

        temp_parsed = Path(mock_config['output']['dir']) / "parsed.json"
        temp_parsed.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_parsed, 'w', encoding='utf-8') as f:
            json.dump(mock_result, f, ensure_ascii=False)

        mock_config['input']['parsed_data_path'] = str(temp_parsed)

        result = excel_parse(mock_config)

        # 驗證輸出文件存在
        assert Path(result['parsed_data_path']).exists()

        # 驗證輸出內容
        with open(result['parsed_data_path'], 'r', encoding='utf-8') as f:
            saved_data = json.load(f)

        assert 'title' in saved_data
        assert 'cells' in saved_data

        print("\n✓ 輸出結構測試通過")
        print(f"  - 輸出文件: {result['parsed_data_path']}")


class TestErrorHandling:
    """測試錯誤處理"""

    def test_file_not_found(self):
        """測試文件不存在的情況"""
        config = {
            'input': {
                'file_path': 'non_existent_file.xlsx'
            },
            'parser': {
                'llm': {
                    'url': 'http://localhost:8074/v1/chat/completions',
                    'model': 'test-model'
                }
            },
            'verbose': False
        }

        result = excel_parse(config)
        assert result['success'] is False
        assert 'error' in result
        print("✓ 文件不存在錯誤處理測試通過")

    def test_invalid_directory(self):
        """測試目錄不存在的情況"""
        config = {
            'input': {
                'input_dir': 'non_existent_directory'
            },
            'parser': {
                'llm': {
                    'url': 'http://localhost:8074/v1/chat/completions',
                    'model': 'test-model'
                }
            },
            'verbose': False
        }

        result = excel_parse(config)
        assert result['success'] is False
        assert 'error' in result
        print("✓ 目錄不存在錯誤處理測試通過")

    def test_both_file_and_dir(self):
        """測試同時提供文件和目錄的情況"""
        config = {
            'input': {
                'file_path': 'test.xlsx',
                'input_dir': 'test_dir'
            },
            'parser': {
                'llm': {
                    'url': 'http://localhost:8074/v1/chat/completions',
                    'model': 'test-model'
                }
            },
            'verbose': False
        }

        result = excel_parse(config)
        assert result['success'] is False
        assert 'error' in result
        print("✓ 同時提供文件和目錄錯誤處理測試通過")


class TestIntegration:
    """整合測試"""

    def test_full_pipeline_structure(self):
        """測試完整 pipeline 的結構（不實際調用 LLM）"""
        test_dir = Path("tests/testcases/excel")
        if not test_dir.exists():
            pytest.skip(f"測試目錄不存在: {test_dir}")

        excel_files = list(test_dir.glob("*.xlsx"))
        if not excel_files:
            pytest.skip("沒有測試文件")

        print(f"\n整合測試：{len(excel_files)} 個 Excel 文件")

        for excel_file in excel_files:
            print(f"\n處理: {excel_file.name}")

            # 1. 載入 Excel
            parser = ExcelParserLLM(
                vllm_url='http://localhost:8074/v1/chat/completions',
                model='test-model'
            )
            excel_data = parser.load_excel(excel_file)
            print(f"  ✓ 載入成功: {len(excel_data['cells'])} 個儲存格")

            # 2. 模擬解析結果
            mock_cells = []
            for cell in excel_data['cells'][:10]:
                cell_with_analysis = cell.copy()
                cell_with_analysis['x-axis id 意思'] = f"X軸意義-{cell['address']}"
                cell_with_analysis['y-axis id 意思'] = f"Y軸意義-{cell['address']}"
                cell_with_analysis['值'] = cell['value']
                mock_cells.append(cell_with_analysis)

            mock_parsed = {
                'file_name': excel_data['file_name'],
                'sheet_name': excel_data['sheet_name'],
                'title': f"{excel_file.stem} 測試標題",
                'x-axis': 'X軸說明',
                'y-axis': 'Y軸說明',
                'file_path': str(excel_file),
                'cells': mock_cells
            }
            print(f"  ✓ 模擬解析: {len(mock_parsed['cells'])} 個儲存格")

            # 3. 轉換為 AugmenterInput
            augmenter_inputs = ExcelParserLLM.transform_to_augmenterInput(mock_parsed)
            print(f"  ✓ 轉換成功: {len(augmenter_inputs)} 個 AugmenterInput")

            # 4. 驗證結構
            assert len(augmenter_inputs) > 0
            for aug_input in augmenter_inputs:
                assert 'source' in aug_input
                assert 'source_path' in aug_input
                assert 'table_title' in aug_input['source']
                assert '值' in aug_input['source']

        print(f"\n✓ 整合測試通過：成功處理 {len(excel_files)} 個文件")


def test_batch_consistency():
    """測試批次處理的一致性"""
    test_dir = Path("tests/testcases/excel")
    if not test_dir.exists():
        pytest.skip(f"測試目錄不存在: {test_dir}")

    excel_files = list(test_dir.glob("*.xlsx"))
    if len(excel_files) < 2:
        pytest.skip("需要至少 2 個測試文件")

    parser = ExcelParserLLM(
        vllm_url='http://localhost:8074/v1/chat/completions',
        model='test-model'
    )

    # 單獨處理每個文件
    individual_results = []
    for excel_file in excel_files:
        excel_data = parser.load_excel(excel_file)
        individual_results.append({
            'file': excel_file.name,
            'cells_count': len(excel_data['cells'])
        })

    # 批次處理
    batch_cells = []
    for excel_file in excel_files:
        excel_data = parser.load_excel(excel_file)
        batch_cells.extend(excel_data['cells'])

    # 驗證一致性
    total_individual = sum(r['cells_count'] for r in individual_results)
    assert len(batch_cells) == total_individual

    print(f"\n✓ 批次一致性測試通過")
    print(f"  - 文件數: {len(excel_files)}")
    print(f"  - 總儲存格數: {len(batch_cells)}")


if __name__ == '__main__':
    """直接執行測試（不使用 pytest）"""
    print("=" * 70)
    print("Excel Pipeline 完整測試")
    print("=" * 70)

    # 手動運行一些基本測試
    test_excel = TestExcelParser()
    test_pipeline = TestExcelPipeline()
    test_errors = TestErrorHandling()
    test_integration = TestIntegration()

    test_dir = Path("tests/testcases/excel")
    if test_dir.exists():
        excel_files = list(test_dir.glob("*.xlsx"))

        print(f"\n找到 {len(excel_files)} 個測試文件:")
        for f in excel_files:
            print(f"  - {f.name}")

        # 運行基本測試
        try:
            print("\n" + "=" * 70)
            print("1. Excel Parser 初始化測試")
            print("=" * 70)
            test_excel.test_excel_parser_initialization()

            print("\n" + "=" * 70)
            print("2. 欄位名稱轉換測試")
            print("=" * 70)
            test_excel.test_column_name_conversion()

            print("\n" + "=" * 70)
            print("3. 載入 Excel 文件測試")
            print("=" * 70)
            test_excel.test_load_excel_single_file(excel_files)

            print("\n" + "=" * 70)
            print("4. 批次載入測試")
            print("=" * 70)
            test_excel.test_load_excel_batch()

            print("\n" + "=" * 70)
            print("5. 轉換為 AugmenterInput 測試")
            print("=" * 70)
            test_excel.test_transform_to_augmenter_input(excel_files)

            print("\n" + "=" * 70)
            print("6. 錯誤處理測試")
            print("=" * 70)
            test_errors.test_file_not_found()
            test_errors.test_invalid_directory()
            test_errors.test_both_file_and_dir()

            print("\n" + "=" * 70)
            print("7. 整合測試")
            print("=" * 70)
            test_integration.test_full_pipeline_structure()

            print("\n" + "=" * 70)
            print("8. 批次一致性測試")
            print("=" * 70)
            test_batch_consistency()

            print("\n" + "=" * 70)
            print("測試總結")
            print("=" * 70)
            print("✓ 所有測試通過！")
            print("\n測試涵蓋:")
            print("  - Excel Parser 基本功能")
            print("  - 單文件和批次模式")
            print("  - 數據轉換和結構驗證")
            print("  - 錯誤處理機制")
            print("  - 完整 pipeline 整合")
            print("=" * 70)

        except Exception as e:
            print(f"\n✗ 測試失敗: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        print(f"\n警告: 測試目錄不存在 - {test_dir}")
        print("請確保測試文件位於正確位置")
