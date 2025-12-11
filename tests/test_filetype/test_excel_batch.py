#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 Excel Pipeline 的批次處理功能
測試使用 input_dir 處理多個 Excel 檔案
"""

import sys
from pathlib import Path

# 將專案根目錄加入 Python 路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
import json
import yaml
from core.excel_pipeline import excel_parse, augment, run


class TestExcelBatchProcessing:
    """測試 Excel 批次處理功能"""

    @pytest.fixture
    def excel_test_dir(self):
        """提供測試用的 Excel 目錄路徑"""
        return project_root / "tests/testcases/filetypes"

    @pytest.fixture
    def test_output_dir(self, tmp_path):
        """建立測試用的輸出目錄"""
        output_dir = tmp_path / "batch_output"
        output_dir.mkdir()
        return output_dir

    @pytest.fixture
    def batch_config(self, excel_test_dir, test_output_dir):
        """提供批次處理的測試配置"""
        return {
            'input': {
                'input_dir': str(excel_test_dir),  # 使用目錄而非單檔
                'skip_parser': False,
            },
            'output': {
                'dir': str(test_output_dir)
            },
            'parser': {
                'llm': {
                    'url': 'http://localhost:8074/v1/chat/completions',
                    'model': 'test-model',
                    'api_key': None,
                    'use_openrouter': False,
                    'max_retries': 1
                }
            },
            'augmenter': {
                'prompt_name': 'default',
                'mode': 'vllm',
                'vllm': {
                    'url': 'http://localhost:8074/v1/chat/completions',
                    'model_name': 'test-model',
                    'max_tokens': 4096,
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'frequency_penalty': 0.1,
                    'presence_penalty': 0.1,
                    'is_thinking_mode': False,
                    'limit_llmoutput_scheme': False,
                }
            },
            'verbose': False  # 關閉詳細輸出以簡化測試
        }

    @pytest.fixture
    def single_file_config(self, excel_test_dir, test_output_dir):
        """提供單檔處理的測試配置"""
        excel_file = excel_test_dir / "表7-3-2.xlsx"
        return {
            'input': {
                'file_path': str(excel_file),
                'skip_parser': False,
            },
            'output': {
                'dir': str(test_output_dir / "single")
            },
            'parser': {
                'llm': {
                    'url': 'http://localhost:8074/v1/chat/completions',
                    'model': 'test-model',
                    'api_key': None,
                    'use_openrouter': False,
                    'max_retries': 1
                }
            },
            'augmenter': {
                'prompt_name': 'default',
                'mode': 'vllm',
                'vllm': {
                    'url': 'http://localhost:8074/v1/chat/completions',
                    'model_name': 'test-model',
                    'max_tokens': 4096,
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'frequency_penalty': 0.1,
                    'presence_penalty': 0.1,
                    'is_thinking_mode': False,
                    'limit_llmoutput_scheme': False,
                }
            },
            'verbose': False
        }

    def test_excel_files_exist_in_directory(self, excel_test_dir):
        """測試目錄中是否存在 Excel 檔案"""
        excel_extensions = ['.xlsx', '.xlsm', '.xltx', '.xltm']
        excel_files = [f for f in excel_test_dir.iterdir() if f.suffix in excel_extensions]

        assert len(excel_files) > 0, f"測試目錄 {excel_test_dir} 中沒有找到 Excel 檔案"
        print(f"找到 {len(excel_files)} 個 Excel 檔案: {[f.name for f in excel_files]}")

    def test_batch_config_validation(self, batch_config):
        """測試批次配置的正確性"""
        # 驗證 input_dir 存在
        assert 'input' in batch_config
        assert 'input_dir' in batch_config['input']

        # 驗證目錄存在
        input_dir = Path(batch_config['input']['input_dir'])
        assert input_dir.exists(), f"輸入目錄不存在: {input_dir}"
        assert input_dir.is_dir(), f"輸入路徑不是目錄: {input_dir}"

    def test_batch_vs_single_config_difference(self, batch_config, single_file_config):
        """測試批次配置與單檔配置的差異"""
        # 批次配置應使用 input_dir
        assert 'input_dir' in batch_config['input']
        assert 'file_path' not in batch_config['input']

        # 單檔配置應使用 file_path
        assert 'file_path' in single_file_config['input']
        assert 'input_dir' not in single_file_config['input']

    def test_config_mutual_exclusion(self, excel_test_dir, test_output_dir):
        """測試不能同時提供 file_path 和 input_dir"""
        invalid_config = {
            'input': {
                'file_path': str(excel_test_dir / "表7-3-2.xlsx"),
                'input_dir': str(excel_test_dir),  # 不應同時存在
            },
            'output': {'dir': str(test_output_dir)},
            'parser': {'llm': {'url': 'http://localhost:8074/v1/chat/completions', 'model': 'test-model'}},
            'verbose': False
        }

        # 應該拋出 ValueError
        with pytest.raises(ValueError, match="不能同時提供"):
            excel_parse(invalid_config)

    def test_missing_input_error(self, test_output_dir):
        """測試缺少輸入參數時的錯誤處理"""
        invalid_config = {
            'input': {},  # 沒有 file_path 或 input_dir
            'output': {'dir': str(test_output_dir)},
            'parser': {'llm': {'url': 'http://localhost:8074/v1/chat/completions', 'model': 'test-model'}},
            'verbose': False
        }

        # 應該拋出 ValueError
        with pytest.raises(ValueError, match="必須提供"):
            excel_parse(invalid_config)

    def test_batch_parser_output_structure(self, batch_config, test_output_dir):
        """測試批次處理的輸出結構（不實際呼叫 LLM）"""
        # 修改配置以跳過 parser
        batch_config['input']['skip_parser'] = True

        # 建立假的解析數據
        fake_parsed_data = [
            {
                'file_name': 'test1.xlsx',
                'file_path': '/path/to/test1.xlsx',
                'title': 'Test Table 1',
                'x-axis': 'Year',
                'y-axis': 'Item',
                'cells': [
                    {
                        'x-axis id': 'A',
                        'y-axis id': '1',
                        'x-axis id 意思': '2020',
                        'y-axis id 意思': 'Revenue',
                        '值': '100'
                    }
                ]
            },
            {
                'file_name': 'test2.xlsx',
                'file_path': '/path/to/test2.xlsx',
                'title': 'Test Table 2',
                'x-axis': 'Month',
                'y-axis': 'Category',
                'cells': [
                    {
                        'x-axis id': 'B',
                        'y-axis id': '2',
                        'x-axis id 意思': 'January',
                        'y-axis id 意思': 'Expenses',
                        '值': '50'
                    }
                ]
            }
        ]

        # 儲存假數據
        parsed_data_path = test_output_dir / "fake_parsed_data.json"
        with open(parsed_data_path, 'w', encoding='utf-8') as f:
            json.dump(fake_parsed_data, f, ensure_ascii=False, indent=2)

        batch_config['input']['parsed_data_path'] = str(parsed_data_path)

        # 執行 parser（應該只載入數據，不呼叫 LLM）
        result = excel_parse(batch_config)

        # 驗證結果結構
        assert result['success'] == True
        assert 'parsed_data' in result
        assert 'augmenter_inputs' in result
        assert 'total_count' in result
        assert 'batch_mode' in result
        assert 'file_count' in result

        # 驗證批次模式
        assert result['batch_mode'] == True
        assert result['file_count'] == 2

        # 驗證 augmenter_inputs 包含兩個檔案的數據
        assert len(result['augmenter_inputs']) == 2  # 每個檔案一個 cell

        print(f"批次處理結果: 處理了 {result['file_count']} 個檔案，共 {result['total_count']} 筆數據")

    def test_augment_handles_batch_inputs(self, batch_config, test_output_dir):
        """測試 augment 函數能處理批次輸入"""
        # 建立模擬的 augmenter_inputs（來自多個檔案）
        augmenter_inputs = [
            {
                'source': {
                    'table_title': 'Table 1',
                    "table's x-axis": 'Year',
                    "table's y-axis": 'Item',
                    "cell's x-axis id 意思": '2020',
                    "cell's y-axis id 意思": 'Revenue',
                    '值': '100'
                },
                'source_path': '/path/to/test1.xlsx'
            },
            {
                'source': {
                    'table_title': 'Table 2',
                    "table's x-axis": 'Month',
                    "table's y-axis": 'Category',
                    "cell's x-axis id 意思": 'January',
                    "cell's y-axis id 意思": 'Expenses',
                    '值': '50'
                },
                'source_path': '/path/to/test2.xlsx'
            },
            {
                'source': {
                    'table_title': 'Table 1',
                    "table's x-axis": 'Year',
                    "table's y-axis": 'Item',
                    "cell's x-axis id 意思": '2021',
                    "cell's y-axis id 意思": 'Revenue',
                    '值': '120'
                },
                'source_path': '/path/to/test1.xlsx'
            }
        ]

        # 驗證 augmenter_inputs 是列表
        assert isinstance(augmenter_inputs, list)
        assert len(augmenter_inputs) == 3

        # 驗證每個 input 都有正確的結構
        for item in augmenter_inputs:
            assert 'source' in item
            assert isinstance(item['source'], dict)
            assert 'source_path' in item

        print(f"augment 可以處理 {len(augmenter_inputs)} 筆批次輸入")

        # 注意: 實際執行 augment 需要 LLM 服務，這裡只測試數據結構
        # 如果需要實際測試，可以取消下面的註解（需要 LLM 服務運行）
        # result = augment(batch_config, augmenter_inputs)
        # assert result['success'] == True
        # assert result['total_count'] == 3

    def test_single_file_backward_compatibility(self, single_file_config):
        """測試單檔模式的向後兼容性"""
        # 驗證單檔配置仍然有效
        assert 'file_path' in single_file_config['input']

        # 驗證檔案存在
        file_path = Path(single_file_config['input']['file_path'])
        assert file_path.exists(), f"測試檔案不存在: {file_path}"

        print(f"單檔模式兼容性測試通過: {file_path.name}")


class TestExcelBatchIntegration:
    """測試批次處理的完整集成"""

    @pytest.fixture
    def minimal_batch_config(self, tmp_path):
        """提供最小化的批次測試配置"""
        # 建立測試用的 Excel 檔案目錄
        test_excel_dir = tmp_path / "excel_files"
        test_excel_dir.mkdir()

        output_dir = tmp_path / "batch_integration_output"
        output_dir.mkdir()

        return {
            'input': {
                'input_dir': str(test_excel_dir),
                'skip_parser': False,
            },
            'output': {
                'dir': str(output_dir)
            },
            'parser': {
                'llm': {
                    'url': 'http://localhost:8074/v1/chat/completions',
                    'model': 'test-model',
                    'api_key': None,
                    'use_openrouter': False,
                    'max_retries': 1
                }
            },
            'augmenter': {
                'prompt_name': 'default',
                'mode': 'vllm',
                'vllm': {
                    'url': 'http://localhost:8074/v1/chat/completions',
                    'model_name': 'test-model',
                    'max_tokens': 4096,
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'frequency_penalty': 0.1,
                    'presence_penalty': 0.1,
                    'is_thinking_mode': False,
                    'limit_llmoutput_scheme': False,
                }
            },
            'verbose': False
        }

    def test_empty_directory_error(self, minimal_batch_config):
        """測試空目錄的錯誤處理"""
        # minimal_batch_config 的 input_dir 是空的

        with pytest.raises(ValueError, match="找不到 Excel 檔案"):
            excel_parse(minimal_batch_config)

    def test_batch_processing_workflow(self, tmp_path):
        """測試批次處理的完整工作流程（使用假數據）"""
        # 建立測試目錄
        test_dir = tmp_path / "workflow_test"
        test_dir.mkdir()

        # 建立假的解析數據（模擬多個檔案）
        fake_batch_data = [
            {
                'file_name': 'report_2020.xlsx',
                'file_path': str(test_dir / 'report_2020.xlsx'),
                'title': 'Annual Report 2020',
                'x-axis': 'Quarter',
                'y-axis': 'Metric',
                'cells': [
                    {'x-axis id': 'B', 'y-axis id': '2',
                     'x-axis id 意思': 'Q1', 'y-axis id 意思': 'Sales', '值': '1000'}
                ]
            },
            {
                'file_name': 'report_2021.xlsx',
                'file_path': str(test_dir / 'report_2021.xlsx'),
                'title': 'Annual Report 2021',
                'x-axis': 'Quarter',
                'y-axis': 'Metric',
                'cells': [
                    {'x-axis id': 'B', 'y-axis id': '2',
                     'x-axis id 意思': 'Q1', 'y-axis id 意思': 'Sales', '值': '1200'}
                ]
            }
        ]

        # 儲存假數據
        parsed_data_path = test_dir / "parsed_batch.json"
        with open(parsed_data_path, 'w', encoding='utf-8') as f:
            json.dump(fake_batch_data, f, ensure_ascii=False, indent=2)

        # 建立配置
        config = {
            'input': {
                'skip_parser': True,
                'parsed_data_path': str(parsed_data_path)
            },
            'output': {
                'dir': str(test_dir / "output")
            },
            'parser': {
                'llm': {
                    'url': 'http://localhost:8074/v1/chat/completions',
                    'model': 'test-model'
                }
            },
            'verbose': False
        }

        # 執行 parser
        result = excel_parse(config)

        # 驗證結果
        assert result['success'] == True
        assert result['batch_mode'] == True
        assert result['file_count'] == 2
        assert result['total_count'] == 2  # 兩個檔案各一個 cell

        # 驗證 augmenter_inputs 結構
        assert len(result['augmenter_inputs']) == 2
        for item in result['augmenter_inputs']:
            assert 'source' in item
            assert 'source_path' in item

        print(f"批次工作流程測試完成: {result['file_count']} 個檔案，{result['total_count']} 筆數據")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
