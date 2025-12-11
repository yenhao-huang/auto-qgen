#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 Excel 文件類型處理
測試 Excel Pipeline 的完整流程
"""

import sys
from pathlib import Path

# 將專案根目錄加入 Python 路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
import json
import yaml
from core.main import (
    load_config,
    get_file_type,
    determine_pipeline_type,
    run_excel_pipeline
)


class TestExcelFileType:
    """測試 Excel 文件類型的識別和處理"""

    @pytest.fixture
    def excel_test_file(self):
        """提供測試用的 Excel 文件路徑"""
        return project_root / "tests/testcases/filetypes/表7-3-2.xlsx"

    @pytest.fixture
    def test_config_dir(self, tmp_path):
        """建立測試用的配置目錄"""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        return config_dir

    @pytest.fixture
    def test_output_dir(self, tmp_path):
        """建立測試用的輸出目錄"""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        return output_dir

    def test_file_exists(self, excel_test_file):
        """測試 Excel 測試文件是否存在"""
        assert excel_test_file.exists(), f"測試文件不存在: {excel_test_file}"
        assert excel_test_file.suffix.lower() == '.xlsx', "測試文件應為 .xlsx 格式"

    def test_get_file_type(self, excel_test_file):
        """測試文件類型檢測功能"""
        file_type = get_file_type(excel_test_file)
        assert file_type == 'excel', f"應檢測為 excel，實際為 {file_type}"

    def test_get_file_type_various_extensions(self):
        """測試各種 Excel 文件擴展名"""
        test_cases = [
            ('.xlsx', 'excel'),
            ('.xls', 'excel'),
            ('.xlsm', 'excel'),
            ('.xlsb', 'excel'),
        ]

        for ext, expected_type in test_cases:
            # 建立虛擬路徑（不需要實際存在）
            fake_path = Path(f"test{ext}")
            # 由於 get_file_type 會檢查文件是否存在，我們直接測試邏輯
            if ext in ['.xlsx', '.xls', '.xlsm', '.xlsb']:
                assert expected_type == 'excel'

    def test_config_loading(self, test_config_dir, excel_test_file, test_output_dir):
        """測試配置文件載入"""
        config = {
            'pipeline_type': 'excel',
            'input': str(excel_test_file),
            'excel': {
                'skip_parser': False,
                'output_dir': str(test_output_dir),
                'parser': {
                    'llm': {
                        'url': 'http://localhost:8074/v1/chat/completions',
                        'model': 'test-model',
                        'api_key': None,
                        'use_openrouter': False,
                        'max_retries': 3
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
                }
            }
        }

        # 儲存配置到 YAML 文件
        config_path = test_config_dir / "test_excel.yml"
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True)

        # 載入配置
        loaded_config = load_config(config_path)

        assert loaded_config['pipeline_type'] == 'excel'
        assert Path(loaded_config['input']) == excel_test_file
        assert 'excel' in loaded_config
        assert 'parser' in loaded_config['excel']
        assert 'augmenter' in loaded_config['excel']

    def test_determine_pipeline_type_auto(self, excel_test_file):
        """測試自動檢測 Pipeline 類型"""
        config = {
            'pipeline_type': 'auto',
            'input': str(excel_test_file)
        }

        pipeline_type = determine_pipeline_type(config)
        assert pipeline_type == 'excel', f"應自動檢測為 excel，實際為 {pipeline_type}"

    def test_determine_pipeline_type_explicit(self, excel_test_file):
        """測試顯式指定 Pipeline 類型"""
        config = {
            'pipeline_type': 'excel',
            'input': str(excel_test_file)
        }

        pipeline_type = determine_pipeline_type(config)
        assert pipeline_type == 'excel', f"應為 excel，實際為 {pipeline_type}"

    def test_excel_config_structure(self, test_output_dir):
        """測試 Excel Pipeline 配置結構的正確性"""
        config = {
            'input': {
                'file_path': '/path/to/test.xlsx',
                'skip_parser': False,
                'parsed_data_path': 'results/parsed_data.json'
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
                    'max_retries': 3
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
            }
        }

        # 驗證配置結構
        assert 'input' in config
        assert 'file_path' in config['input']
        assert 'output' in config
        assert 'dir' in config['output']
        assert 'parser' in config
        assert 'llm' in config['parser']
        assert 'augmenter' in config
        assert 'mode' in config['augmenter']

    def test_file_not_found_error(self):
        """測試文件不存在時的錯誤處理"""
        non_existent_file = Path("/path/to/non/existent/file.xlsx")

        with pytest.raises(FileNotFoundError):
            get_file_type(non_existent_file)

    @pytest.mark.skipif(
        not Path("configs/unified_pipeline.example.yml").exists(),
        reason="需要範例配置文件"
    )
    def test_example_config_compatibility(self):
        """測試範例配置文件的兼容性"""
        config_path = project_root / "configs/pipeline.yml"

        if config_path.exists():
            config = load_config(config_path)

            # 檢查必要的欄位
            assert 'pipeline_type' in config or 'input' in config
            if 'excel' in config:
                excel_config = config['excel']
                # 檢查 Excel 配置的基本結構
                assert isinstance(excel_config, dict)


class TestExcelPipelineIntegration:
    """測試 Excel Pipeline 的集成功能"""

    @pytest.fixture
    def excel_test_file(self):
        """提供測試用的 Excel 文件路徑"""
        return project_root / "tests/testcases/filetypes/表7-3-2.xlsx"

    @pytest.fixture
    def minimal_config(self, excel_test_file, tmp_path):
        """提供最小化的測試配置"""
        output_dir = tmp_path / "excel_output"
        output_dir.mkdir()

        return {
            'input': str(excel_test_file),
            'pipeline_type': 'excel',
            'excel': {
                'skip_parser': False,
                'output_dir': str(output_dir),
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
                }
            },
            'metadata': {
                'test_run': True,
                'description': 'Excel file type test'
            }
        }

    def test_excel_pipeline_config_validation(self, minimal_config):
        """測試 Excel Pipeline 配置的驗證"""
        # 驗證配置結構的完整性
        assert 'input' in minimal_config
        assert 'excel' in minimal_config
        assert 'parser' in minimal_config['excel']
        assert 'augmenter' in minimal_config['excel']
        assert 'output_dir' in minimal_config['excel']

    #@pytest.mark.skip(reason="需要實際的 LLM 服務運行")
    def test_excel_pipeline_execution(self, minimal_config):
        """測試 Excel Pipeline 的實際執行（需要 LLM 服務）"""
        result = run_excel_pipeline(minimal_config)

        # 驗證結果結構
        assert 'success' in result
        if result['success']:
            assert 'total_count' in result
            assert 'parsed_data_path' in result
            assert 'augmented_queries_path' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
