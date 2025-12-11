#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 PDF 文件類型處理
測試 PDF Pipeline 的完整流程，包括 PDF 轉圖片、OCR 和問題生成
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
    run_pdf_pipeline
)
from lib.utils.pdf_to_image import PDFToImageConverter


class TestPDFFileType:
    """測試 PDF 文件類型的識別和處理"""

    @pytest.fixture
    def pdf_test_file(self):
        """提供測試用的 PDF 文件路徑"""
        return project_root / "tests/testcases/filetypes/(公告)109年度獎助布建住宿式長照機構公共化資源計畫.pdf"

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

    def test_file_exists(self, pdf_test_file):
        """測試 PDF 測試文件是否存在"""
        assert pdf_test_file.exists(), f"測試文件不存在: {pdf_test_file}"
        assert pdf_test_file.suffix.lower() == '.pdf', "測試文件應為 .pdf 格式"

    def test_get_file_type(self, pdf_test_file):
        """測試文件類型檢測功能"""
        file_type = get_file_type(pdf_test_file)
        assert file_type == 'pdf', f"應檢測為 pdf，實際為 {file_type}"

    def test_config_loading(self, test_config_dir, pdf_test_file, test_output_dir):
        """測試配置文件載入"""
        config = {
            'pipeline_type': 'pdf',
            'input': str(pdf_test_file),
            'pdf': {
                'conversion': {
                    'dpi': 200,
                    'format': 'PNG',
                    'max_size': 1024
                },
                'ocr': {
                    'output_dir': str(test_output_dir / 'pdf_ocr'),
                    'engine': 'paddle',
                    'mode': 'vllm',
                    'vllm': {
                        'url': 'http://localhost:3264/v1/chat/completions',
                        'model_name': 'test-model',
                        'max_tokens': 4096,
                        'temperature': 0.7,
                        'top_p': 0.9,
                        'frequency_penalty': 0.1,
                        'presence_penalty': 0.1,
                        'timeout': 3600
                    },
                    'recursive': True
                },
                'gen_ques': {
                    'output_dir': str(test_output_dir / 'pdf_gen_ques'),
                    'mode': 'vllm',
                    'vllm': {
                        'url': 'http://localhost:8074/v1/chat/completions',
                        'model_name': 'test-model',
                        'max_tokens': 4096,
                        'temperature': 0.7,
                        'top_p': 0.9,
                        'frequency_penalty': 0.1,
                        'presence_penalty': 0.1,
                        'is_thinking_mode': True,
                        'limit_llmoutput_scheme': False
                    },
                    'prompt_name': 'default',
                    'verify_connection': False
                },
                'ocr_only': False
            }
        }

        # 儲存配置到 YAML 文件
        config_path = test_config_dir / "test_pdf.yml"
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True)

        # 載入配置
        loaded_config = load_config(config_path)

        assert loaded_config['pipeline_type'] == 'pdf'
        assert Path(loaded_config['input']) == pdf_test_file
        assert 'pdf' in loaded_config
        assert 'conversion' in loaded_config['pdf']
        assert 'ocr' in loaded_config['pdf']
        assert 'gen_ques' in loaded_config['pdf']

    def test_determine_pipeline_type_auto(self, pdf_test_file):
        """測試自動檢測 Pipeline 類型"""
        config = {
            'pipeline_type': 'auto',
            'input': str(pdf_test_file)
        }

        pipeline_type = determine_pipeline_type(config)
        assert pipeline_type == 'pdf', f"應自動檢測為 pdf，實際為 {pipeline_type}"

    def test_determine_pipeline_type_explicit(self, pdf_test_file):
        """測試顯式指定 Pipeline 類型"""
        config = {
            'pipeline_type': 'pdf',
            'input': str(pdf_test_file)
        }

        pipeline_type = determine_pipeline_type(config)
        assert pipeline_type == 'pdf', f"應為 pdf，實際為 {pipeline_type}"

    def test_pdf_config_structure(self, test_output_dir):
        """測試 PDF Pipeline 配置結構的正確性"""
        config = {
            'conversion': {
                'dpi': 200,
                'format': 'PNG',
                'max_size': 1024
            },
            'ocr': {
                'output_dir': str(test_output_dir / 'pdf_ocr'),
                'engine': 'paddle',
                'mode': 'vllm',
                'recursive': True
            },
            'gen_ques': {
                'output_dir': str(test_output_dir / 'pdf_gen_ques'),
                'mode': 'vllm',
                'prompt_name': 'default',
                'verify_connection': False
            },
            'ocr_only': False
        }

        # 驗證配置結構
        assert 'conversion' in config
        assert 'dpi' in config['conversion']
        assert 'format' in config['conversion']
        assert 'max_size' in config['conversion']
        assert 'ocr' in config
        assert 'gen_ques' in config
        assert 'ocr_only' in config

    def test_pdf_conversion_settings(self):
        """測試 PDF 轉換設定"""
        test_cases = [
            {'dpi': 150, 'format': 'PNG', 'max_size': 800},
            {'dpi': 200, 'format': 'PNG', 'max_size': 1024},
            {'dpi': 300, 'format': 'JPEG', 'max_size': 1536},
        ]

        for settings in test_cases:
            config = {
                'conversion': settings
            }
            assert config['conversion']['dpi'] == settings['dpi']
            assert config['conversion']['format'] == settings['format']
            assert config['conversion']['max_size'] == settings['max_size']

    def test_file_not_found_error(self):
        """測試文件不存在時的錯誤處理"""
        non_existent_file = Path("/path/to/non/existent/file.pdf")

        with pytest.raises(FileNotFoundError):
            get_file_type(non_existent_file)
    '''
    @pytest.mark.skipif(
        not Path("configs/pipeline.yml").exists(),
        reason="需要範例配置文件"
    )
    '''
    def test_example_config_compatibility(self):
        """測試範例配置文件的兼容性"""
        config_path = project_root / "configs/pipeline.yml"

        if config_path.exists():
            config = load_config(config_path)

            # 檢查必要的欄位
            assert 'pipeline_type' in config or 'input' in config
            if 'pdf' in config:
                pdf_config = config['pdf']
                # 檢查 PDF 配置的基本結構
                assert isinstance(pdf_config, dict)
                assert 'conversion' in pdf_config or 'ocr' in pdf_config


class TestPDFConversion:
    """測試 PDF 轉圖片功能"""

    @pytest.fixture
    def pdf_test_file(self):
        """提供測試用的 PDF 文件路徑"""
        return project_root / "tests/testcases/filetypes/(公告)109年度獎助布建住宿式長照機構公共化資源計畫.pdf"

    @pytest.fixture
    def converter(self):
        """建立 PDF 轉圖片轉換器"""
        return PDFToImageConverter(dpi=200, max_size=1024, fmt='PNG')

    def test_converter_initialization(self, converter):
        """測試轉換器初始化"""
        assert converter is not None
        assert hasattr(converter, 'convert')

    def test_converter_parameters(self):
        """測試轉換器參數設定"""
        test_params = [
            {'dpi': 150, 'max_size': 800, 'fmt': 'PNG'},
            {'dpi': 200, 'max_size': 1024, 'fmt': 'PNG'},
            {'dpi': 300, 'max_size': 1536, 'fmt': 'JPEG'},
        ]

        for params in test_params:
            converter = PDFToImageConverter(
                dpi=params['dpi'],
                max_size=params['max_size'],
                fmt=params['fmt']
            )
            assert converter is not None

    #@pytest.mark.skip(reason="需要實際的 PDF 文件和處理環境")
    def test_pdf_conversion_execution(self, pdf_test_file, converter, tmp_path):
        """測試 PDF 轉圖片的實際執行"""
        output_dir = tmp_path / "pdf_images"
        output_dir.mkdir()

        result = converter.convert(
            pdf_path=str(pdf_test_file),
            output_dir=str(output_dir),
            filename_prefix="test"
        )

        # 驗證結果
        assert result is not None
        assert hasattr(result, 'status')


class TestPDFPipelineIntegration:
    """測試 PDF Pipeline 的集成功能"""

    @pytest.fixture
    def pdf_test_file(self):
        """提供測試用的 PDF 文件路徑"""
        return project_root / "tests/testcases/filetypes/(公告)109年度獎助布建住宿式長照機構公共化資源計畫.pdf"

    @pytest.fixture
    def minimal_config(self, pdf_test_file, tmp_path):
        """提供最小化的測試配置"""
        output_dir = tmp_path / "pdf_output"
        output_dir.mkdir()

        return {
            'input': str(pdf_test_file),
            'pipeline_type': 'pdf',
            'pdf': {
                'conversion': {
                    'dpi': 200,
                    'format': 'PNG',
                    'max_size': 1024
                },
                'ocr': {
                    'output_dir': str(output_dir / 'pdf_ocr'),
                    'engine': 'paddle',
                    'mode': 'vllm',
                    'vllm': {
                        'url': 'http://localhost:3264/v1/chat/completions',
                        'model_name': 'test-model',
                        'max_tokens': 4096,
                        'temperature': 0.7,
                        'top_p': 0.9,
                        'frequency_penalty': 0.1,
                        'presence_penalty': 0.1,
                        'timeout': 3600
                    },
                    'recursive': True
                },
                'gen_ques': {
                    'output_dir': str(output_dir / 'pdf_gen_ques'),
                    'mode': 'vllm',
                    'vllm': {
                        'url': 'http://localhost:8074/v1/chat/completions',
                        'model_name': 'test-model',
                        'max_tokens': 4096,
                        'temperature': 0.7,
                        'top_p': 0.9,
                        'frequency_penalty': 0.1,
                        'presence_penalty': 0.1,
                        'is_thinking_mode': True,
                        'limit_llmoutput_scheme': False
                    },
                    'prompt_name': 'default',
                    'verify_connection': False
                },
                'ocr_only': False
            },
            'metadata': {
                'test_run': True,
                'description': 'PDF file type test'
            }
        }

    @pytest.fixture
    def ocr_only_config(self, pdf_test_file, tmp_path):
        """提供只執行 OCR 的測試配置"""
        output_dir = tmp_path / "pdf_ocr_only"
        output_dir.mkdir()

        return {
            'input': str(pdf_test_file),
            'pipeline_type': 'pdf',
            'pdf': {
                'conversion': {
                    'dpi': 200,
                    'format': 'PNG',
                    'max_size': 1024
                },
                'ocr': {
                    'output_dir': str(output_dir / 'pdf_ocr'),
                    'engine': 'paddle',
                    'mode': 'vllm',
                    'vllm': {
                        'url': 'http://localhost:3264/v1/chat/completions',
                        'model_name': 'test-model',
                        'max_tokens': 4096,
                        'temperature': 0.7,
                        'top_p': 0.9,
                        'frequency_penalty': 0.1,
                        'presence_penalty': 0.1,
                        'timeout': 3600
                    },
                    'recursive': True
                },
                'gen_ques': {},
                'ocr_only': True
            },
            'metadata': {
                'test_run': True,
                'description': 'PDF OCR only test'
            }
        }

    def test_pdf_pipeline_config_validation(self, minimal_config):
        """測試 PDF Pipeline 配置的驗證"""
        # 驗證配置結構的完整性
        assert 'input' in minimal_config
        assert 'pdf' in minimal_config
        assert 'conversion' in minimal_config['pdf']
        assert 'ocr' in minimal_config['pdf']
        assert 'gen_ques' in minimal_config['pdf']

    def test_ocr_only_config_validation(self, ocr_only_config):
        """測試 OCR Only 模式的配置驗證"""
        assert 'pdf' in ocr_only_config
        assert 'ocr_only' in ocr_only_config['pdf']
        assert ocr_only_config['pdf']['ocr_only'] is True

    def test_conversion_config_validation(self, minimal_config):
        """測試轉換配置的驗證"""
        conversion_config = minimal_config['pdf']['conversion']

        assert 'dpi' in conversion_config
        assert 'format' in conversion_config
        assert 'max_size' in conversion_config

        assert isinstance(conversion_config['dpi'], int)
        assert isinstance(conversion_config['format'], str)
        assert isinstance(conversion_config['max_size'], int)

    #@pytest.mark.skip(reason="需要實際的 PDF 處理服務運行")
    def test_pdf_pipeline_execution(self, minimal_config):
        """測試 PDF Pipeline 的實際執行（需要 PDF 處理服務）"""
        success = run_pdf_pipeline(minimal_config)

        # 驗證執行結果
        assert isinstance(success, bool)

    #@pytest.mark.skip(reason="需要實際的 PDF 處理服務運行")
    def test_ocr_only_execution(self, ocr_only_config):
        """測試只執行 OCR 的流程（需要 PDF 處理服務）"""
        success = run_pdf_pipeline(ocr_only_config)

        # 驗證執行結果
        assert isinstance(success, bool)


class TestPDFFormats:
    """測試 PDF 格式的支援"""

    def test_pdf_format_support(self):
        """測試 PDF 格式支援"""
        test_file = Path("test.pdf")
        suffix = test_file.suffix.lower()
        assert suffix == '.pdf'

    def test_output_image_formats(self):
        """測試支援的輸出圖片格式"""
        supported_formats = ['PNG', 'JPEG', 'JPG']

        for fmt in supported_formats:
            config = {
                'conversion': {
                    'format': fmt,
                    'dpi': 200,
                    'max_size': 1024
                }
            }
            assert config['conversion']['format'] in supported_formats


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
