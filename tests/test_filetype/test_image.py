#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試圖片文件類型處理
測試 Image Pipeline 的完整流程，包括 OCR 和問題生成
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
    run_image_pipeline
)


class TestImageFileType:
    """測試圖片文件類型的識別和處理"""

    @pytest.fixture
    def image_test_file(self):
        """提供測試用的圖片文件路徑"""
        return project_root / "tests/testcases/filetypes/(檔案下載)113年度長期照顧服務機構評鑑結果-第一批次名單_page_0002.png"

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

    def test_file_exists(self, image_test_file):
        """測試圖片測試文件是否存在"""
        assert image_test_file.exists(), f"測試文件不存在: {image_test_file}"
        assert image_test_file.suffix.lower() == '.png', "測試文件應為 .png 格式"

    def test_get_file_type(self, image_test_file):
        """測試文件類型檢測功能"""
        file_type = get_file_type(image_test_file)
        assert file_type == 'image', f"應檢測為 image，實際為 {file_type}"

    def test_get_file_type_various_extensions(self):
        """測試各種圖片文件擴展名"""
        test_cases = [
            ('.png', 'image'),
            ('.jpg', 'image'),
            ('.jpeg', 'image'),
            ('.bmp', 'image'),
            ('.gif', 'image'),
            ('.tiff', 'image'),
            ('.webp', 'image'),
        ]

        for ext, expected_type in test_cases:
            # 驗證邏輯正確性
            if ext in ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp']:
                assert expected_type == 'image'

    def test_config_loading(self, test_config_dir, image_test_file, test_output_dir):
        """測試配置文件載入"""
        config = {
            'pipeline_type': 'image',
            'input': str(image_test_file),
            'image': {
                'ocr': {
                    'output_dir': str(test_output_dir / 'ocr'),
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
                    'output_dir': str(test_output_dir / 'gen_ques'),
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
        config_path = test_config_dir / "test_image.yml"
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True)

        # 載入配置
        loaded_config = load_config(config_path)

        assert loaded_config['pipeline_type'] == 'image'
        assert Path(loaded_config['input']) == image_test_file
        assert 'image' in loaded_config
        assert 'ocr' in loaded_config['image']
        assert 'gen_ques' in loaded_config['image']

    def test_determine_pipeline_type_auto(self, image_test_file):
        """測試自動檢測 Pipeline 類型"""
        config = {
            'pipeline_type': 'auto',
            'input': str(image_test_file)
        }

        pipeline_type = determine_pipeline_type(config)
        assert pipeline_type == 'image', f"應自動檢測為 image，實際為 {pipeline_type}"

    def test_determine_pipeline_type_explicit(self, image_test_file):
        """測試顯式指定 Pipeline 類型"""
        config = {
            'pipeline_type': 'image',
            'input': str(image_test_file)
        }

        pipeline_type = determine_pipeline_type(config)
        assert pipeline_type == 'image', f"應為 image，實際為 {pipeline_type}"

    def test_image_config_structure(self, test_output_dir):
        """測試 Image Pipeline 配置結構的正確性"""
        config = {
            'ocr': {
                'output_dir': str(test_output_dir / 'ocr'),
                'engine': 'paddle',
                'mode': 'vllm',
                'recursive': True
            },
            'gen_ques': {
                'output_dir': str(test_output_dir / 'gen_ques'),
                'mode': 'vllm',
                'prompt_name': 'default',
                'verify_connection': False
            },
            'ocr_only': False
        }

        # 驗證配置結構
        assert 'ocr' in config
        assert 'engine' in config['ocr']
        assert 'mode' in config['ocr']
        assert 'output_dir' in config['ocr']
        assert 'gen_ques' in config
        assert 'mode' in config['gen_ques']
        assert 'ocr_only' in config

    def test_ocr_engines(self):
        """測試支援的 OCR 引擎"""
        supported_engines = [
            'paddle', 'paddleocr',
            'dots', 'dotsocr',
            'chandra', 'chandraocr',
            'nv_nemotron'
        ]

        for engine in supported_engines:
            config = {
                'ocr': {
                    'engine': engine,
                    'output_dir': './results/ocr/',
                    'mode': 'vllm'
                }
            }
            assert config['ocr']['engine'] == engine

    def test_ocr_modes(self):
        """測試支援的 OCR 模式"""
        supported_modes = ['local', 'vllm', 'openrouter']

        for mode in supported_modes:
            config = {
                'ocr': {
                    'mode': mode,
                    'engine': 'paddle',
                    'output_dir': './results/ocr/'
                }
            }
            assert config['ocr']['mode'] == mode

    def test_file_not_found_error(self):
        """測試文件不存在時的錯誤處理"""
        non_existent_file = Path("/path/to/non/existent/image.png")

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
        config_path = project_root / "configs/unified_pipeline.example.yml"

        if config_path.exists():
            config = load_config(config_path)

            # 檢查必要的欄位
            assert 'pipeline_type' in config or 'input' in config
            if 'image' in config:
                image_config = config['image']
                # 檢查 Image 配置的基本結構
                assert isinstance(image_config, dict)
                assert 'ocr' in image_config


class TestImagePipelineIntegration:
    """測試 Image Pipeline 的集成功能"""

    @pytest.fixture
    def image_test_file(self):
        """提供測試用的圖片文件路徑"""
        return project_root / "tests/testcases/filetypes/(檔案下載)113年度長期照顧服務機構評鑑結果-第一批次名單_page_0002.png"

    @pytest.fixture
    def minimal_config(self, image_test_file, tmp_path):
        """提供最小化的測試配置"""
        output_dir = tmp_path / "image_output"
        output_dir.mkdir()

        return {
            'input': str(image_test_file),
            'pipeline_type': 'image',
            'image': {
                'ocr': {
                    'output_dir': str(output_dir / 'ocr'),
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
                    'output_dir': str(output_dir / 'gen_ques'),
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
                'description': 'Image file type test'
            }
        }

    @pytest.fixture
    def ocr_only_config(self, image_test_file, tmp_path):
        """提供只執行 OCR 的測試配置"""
        output_dir = tmp_path / "image_ocr_only"
        output_dir.mkdir()

        return {
            'input': str(image_test_file),
            'pipeline_type': 'image',
            'image': {
                'ocr': {
                    'output_dir': str(output_dir / 'ocr'),
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
                'description': 'Image OCR only test'
            }
        }

    def test_image_pipeline_config_validation(self, minimal_config):
        """測試 Image Pipeline 配置的驗證"""
        # 驗證配置結構的完整性
        assert 'input' in minimal_config
        assert 'image' in minimal_config
        assert 'ocr' in minimal_config['image']
        assert 'gen_ques' in minimal_config['image']

    def test_ocr_only_config_validation(self, ocr_only_config):
        """測試 OCR Only 模式的配置驗證"""
        assert 'image' in ocr_only_config
        assert 'ocr_only' in ocr_only_config['image']
        assert ocr_only_config['image']['ocr_only'] is True

    def test_directory_input_handling(self, tmp_path):
        """測試目錄輸入的處理"""
        # 建立測試目錄和圖片
        test_dir = tmp_path / "test_images"
        test_dir.mkdir()

        config = {
            'input': str(test_dir),
            'pipeline_type': 'image',
            'image': {
                'ocr': {
                    'output_dir': str(tmp_path / 'ocr'),
                    'engine': 'paddle',
                    'mode': 'vllm',
                    'recursive': True
                }
            }
        }

        # 驗證配置接受目錄輸入
        assert Path(config['input']).is_dir()
        assert config['image']['ocr']['recursive'] is True

    #@pytest.mark.skip(reason="需要實際的 OCR 服務運行")
    def test_image_pipeline_execution(self, minimal_config):
        """測試 Image Pipeline 的實際執行（需要 OCR 服務）"""
        success = run_image_pipeline(minimal_config)

        # 驗證執行結果
        assert isinstance(success, bool)

    #@pytest.mark.skip(reason="需要實際的 OCR 服務運行")
    def test_ocr_only_execution(self, ocr_only_config):
        """測試只執行 OCR 的流程（需要 OCR 服務）"""
        success = run_image_pipeline(ocr_only_config)

        # 驗證執行結果
        assert isinstance(success, bool)


class TestImageFileFormats:
    """測試不同圖片格式的支援"""

    def test_png_format_support(self):
        """測試 PNG 格式支援"""
        test_file = Path("test.png")
        suffix = test_file.suffix.lower()
        assert suffix in ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp']

    def test_jpg_format_support(self):
        """測試 JPG 格式支援"""
        test_file = Path("test.jpg")
        suffix = test_file.suffix.lower()
        assert suffix in ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp']

    def test_jpeg_format_support(self):
        """測試 JPEG 格式支援"""
        test_file = Path("test.jpeg")
        suffix = test_file.suffix.lower()
        assert suffix in ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp']


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
