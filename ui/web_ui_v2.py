#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web UI V2 for Auto-Gen MultiModel
支援多檔案上傳和批次處理
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import gradio as gr
import json
import shutil
import yaml
import tempfile
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

# 導入 core/main.py 的函數
from core.main import (
    run_excel_pipeline,
    run_image_pipeline,
    run_pdf_pipeline,
    determine_pipeline_type,
    get_file_type
)


class FileProcessor:
    """檔案處理器，管理上傳的檔案和處理流程"""

    def __init__(self):
        self.temp_dir = None
        self.config = None
        self.results = []

    def initialize_temp_dir(self) -> Path:
        """初始化臨時目錄"""
        if self.temp_dir is None or not self.temp_dir.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.temp_dir = Path(f"ui/data/{timestamp}")
            self.temp_dir.mkdir(parents=True, exist_ok=True)
        return self.temp_dir

    def load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """載入配置文件"""
        if config_path is None:
            config_path = "configs/unified_pipeline.example.yml"

        config_file = Path(config_path)
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        else:
            # 使用預設配置
            self.config = self._get_default_config()

        return self.config

    def update_model_config(self, model_name: str, temperature: float = 0.7, max_tokens: int = 4096):
        """根據選擇的 model 更新配置"""
        if self.config is None:
            self.load_config()

        model_configs = {
            'mistralai3': {
                'url': 'http://192.168.1.78:3132/v1/chat/completions',
                'model_name': 'mistralai3'
            },
            'gpt-oss': {
                'url': 'http://192.168.1.78:3111/v1/chat/completions',
                'model_name': 'gpt-oss-20b'
            },
            'gemma3': {
                'url': 'http://192.168.1.78:8074/v1/chat/completions',
                'model_name': 'gemma-12b'
            }
        }

        if model_name not in model_configs:
            return

        model_cfg = model_configs[model_name]

        # 更新 excel.augmenter
        if 'excel' in self.config and 'augmenter' in self.config['excel']:
            if 'vllm' in self.config['excel']['augmenter']:
                self.config['excel']['augmenter']['vllm']['url'] = model_cfg['url']
                self.config['excel']['augmenter']['vllm']['model_name'] = model_cfg['model_name']
                self.config['excel']['augmenter']['vllm']['temperature'] = temperature
                self.config['excel']['augmenter']['vllm']['max_tokens'] = max_tokens

        # 更新 image.gen_ques.vllm
        if 'image' in self.config and 'gen_ques' in self.config['image']:
            if 'vllm' in self.config['image']['gen_ques']:
                self.config['image']['gen_ques']['vllm']['url'] = model_cfg['url']
                self.config['image']['gen_ques']['vllm']['model_name'] = model_cfg['model_name']
                self.config['image']['gen_ques']['vllm']['temperature'] = temperature
                self.config['image']['gen_ques']['vllm']['max_tokens'] = max_tokens

        # 更新 pdf.gen_ques.vllm
        if 'pdf' in self.config and 'gen_ques' in self.config['pdf']:
            if 'vllm' in self.config['pdf']['gen_ques']:
                self.config['pdf']['gen_ques']['vllm']['url'] = model_cfg['url']
                self.config['pdf']['gen_ques']['vllm']['model_name'] = model_cfg['model_name']
                self.config['pdf']['gen_ques']['vllm']['temperature'] = temperature
                self.config['pdf']['gen_ques']['vllm']['max_tokens'] = max_tokens

    def _get_default_config(self) -> Dict[str, Any]:
        """返回預設配置"""
        return {
            'pipeline_type': 'auto',
            'metadata': {
                'source': 'web_ui_v2',
                'created_at': datetime.now().isoformat()
            },
            'excel': {
                'skip_parser': False,
                'output_dir': 'results/web_ui_v2/excel/',
                'parser': {
                    'prompt_name': 'excel_parser',
                    'llm': {
                        'url': 'http://192.168.1.79:8074/v1/chat/completions',
                        'model': 'gemma-12b',
                        'api_key': None,
                        'use_openrouter': False,
                        'max_retries': 3
                    }
                },
                'augmenter': {
                    'prompt_name': 'default',
                    'mode': 'vllm',
                    'vllm': {
                        'url': 'http://192.168.1.79:8074/v1/chat/completions',
                        'model_name': 'gemma-12b',
                        'max_tokens': 4096,
                        'temperature': 0.7,
                        'top_p': 0.9,
                        'is_thinking_mode': True
                    }
                }
            },
            'image': {
                'ocr': {
                    'output_dir': './results/web_ui_v2/ocr/',
                    'engine': 'paddle',
                    'mode': 'vllm',
                    'vllm': {
                        'url': 'http://192.168.1.76:3264/v1/chat/completions',
                        'model_name': '/workspace/llm_model',
                        'max_tokens': 4096
                    },
                    'recursive': True
                },
                'gen_ques': {
                    'output_dir': 'results/web_ui_v2/ocr/',
                    'mode': 'vllm',
                    'vllm': {
                        'url': 'http://192.168.1.79:8074/v1/chat/completions',
                        'model_name': 'gemma-12b',
                        'max_tokens': 4096,
                        'is_thinking_mode': True
                    },
                    'prompt_name': 'default',
                    'verify_connection': False
                },
                'ocr_only': False
            },
            'pdf': {
                'conversion': {
                    'dpi': 200,
                    'format': 'PNG',
                    'max_size': 1024
                },
                'ocr': {
                    'output_dir': './results/web_ui_v2/pdf_ocr/',
                    'engine': 'paddle',
                    'mode': 'vllm',
                    'vllm': {
                        'url': 'http://192.168.1.76:3264/v1/chat/completions',
                        'model_name': '/workspace/llm_model',
                        'max_tokens': 4096
                    },
                    'recursive': True
                },
                'gen_ques': {
                    'output_dir': 'results/web_ui_v2/pdf_ocr/',
                    'mode': 'vllm',
                    'vllm': {
                        'url': 'http://192.168.1.79:8074/v1/chat/completions',
                        'model_name': 'gemma-12b',
                        'max_tokens': 4096,
                        'is_thinking_mode': True
                    },
                    'prompt_name': 'default',
                    'verify_connection': False
                },
                'ocr_only': False
            }
        }

    def save_uploaded_files(self, files: List[Any]) -> Tuple[Path, List[Path]]:
        """
        儲存上傳的檔案到臨時目錄

        Returns:
            (資料夾路徑, 檔案路徑列表)
        """
        if not files:
            raise ValueError("沒有上傳任何檔案")

        temp_dir = self.initialize_temp_dir()
        input_dir = temp_dir / "input"
        input_dir.mkdir(parents=True, exist_ok=True)

        saved_files = []
        for file in files:
            if file is not None:
                src = Path(file.name)
                dst = input_dir / src.name
                shutil.copy2(src, dst)
                saved_files.append(dst)

        return input_dir, saved_files

    def process_files(self, files: List[Any], progress=gr.Progress()) -> Dict[str, Any]:
        """
        處理多個檔案

        Returns:
            處理結果字典
        """
        if not files or all(f is None for f in files):
            return {
                'success': False,
                'error': '請上傳至少一個檔案',
                'results': []
            }

        try:
            progress(0, desc="初始化...")

            # 儲存上傳的檔案
            input_dir, saved_files = self.save_uploaded_files(files)

            progress(0.1, desc=f"已上傳 {len(saved_files)} 個檔案")

            # 載入配置
            if self.config is None:
                self.load_config()

            # 判斷檔案類型（假設所有檔案類型相同）
            file_types = set()
            for file_path in saved_files:
                ftype = get_file_type(file_path)
                if ftype != 'unknown':
                    file_types.add(ftype)

            if len(file_types) == 0:
                return {
                    'success': False,
                    'error': '沒有支援的檔案類型',
                    'results': []
                }

            if len(file_types) > 1:
                return {
                    'success': False,
                    'error': f'不能混合不同類型的檔案，發現的類型: {", ".join(file_types)}',
                    'results': []
                }

            pipeline_type = list(file_types)[0]

            progress(0.2, desc=f"檔案類型: {pipeline_type.upper()}")

            # 設定配置並執行對應的 pipeline
            config = self.config.copy()
            config['input'] = str(input_dir)  # ui/data/{timestamp}/input
            config['pipeline_type'] = pipeline_type

            progress(0.3, desc="開始處理...")

            # 根據類型執行對應的 pipeline
            if pipeline_type == 'excel':
                result = self._process_excel(config, progress)
            elif pipeline_type == 'image':
                result = self._process_image(config, progress)
            elif pipeline_type == 'pdf':
                result = self._process_pdf(config, progress)
            else:
                return {
                    'success': False,
                    'error': f'不支援的檔案類型: {pipeline_type}',
                    'results': []
                }

            progress(1.0, desc="完成!")

            return result

        except Exception as e:
            import traceback
            return {
                'success': False,
                'error': f'處理失敗: {str(e)}',
                'traceback': traceback.format_exc(),
                'results': []
            }

    def _process_excel(self, config: Dict[str, Any], progress) -> Dict[str, Any]:
        """處理 Excel 檔案"""
        progress(0.4, desc="執行 Excel Pipeline...")

        result = run_excel_pipeline(config)

        if not result.get('success'):
            return {
                'success': False,
                'error': result.get('error', '未知錯誤'),
                'results': []
            }

        progress(0.8, desc="讀取生成的問題...")

        # 讀取生成的問題
        questions = self._extract_questions_from_result(result)

        return {
            'success': True,
            'pipeline_type': 'excel',
            'file_count': result.get('file_count', 1),
            'total_count': result.get('total_count', 0),
            'questions': questions,
            'output_path': result.get('augmented_queries_path'),
            'results': [result]
        }

    def _process_image(self, config: Dict[str, Any], progress) -> Dict[str, Any]:
        """處理圖片檔案"""
        progress(0.4, desc="執行圖片 Pipeline...")

        success = run_image_pipeline(config)

        if not success:
            return {
                'success': False,
                'error': '圖片處理失敗',
                'results': []
            }

        progress(0.8, desc="讀取生成的問題...")

        # 讀取生成的問題
        output_dir = Path(config.get('image', {}).get('gen_ques', {}).get('output_dir', 'results/web_ui_v2/ocr/'))
        output_file = output_dir / 'augmented_queries.json'

        questions = []
        if output_file.exists():
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    qs = item.get('questions', [])
                    questions.extend(qs)

        return {
            'success': True,
            'pipeline_type': 'image',
            'questions': questions,
            'output_path': str(output_file) if output_file.exists() else None,
            'results': []
        }

    def _process_pdf(self, config: Dict[str, Any], progress) -> Dict[str, Any]:
        """處理 PDF 檔案"""
        progress(0.4, desc="執行 PDF Pipeline...")

        success = run_pdf_pipeline(config)

        if not success:
            return {
                'success': False,
                'error': 'PDF 處理失敗',
                'results': []
            }

        progress(0.8, desc="讀取生成的問題...")

        # 讀取生成的問題
        output_dir = Path(config.get('pdf', {}).get('gen_ques', {}).get('output_dir', 'results/web_ui_v2/pdf_ocr/'))
        output_file = output_dir / 'augmented_queries.json'

        questions = []
        if output_file.exists():
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    qs = item.get('questions', [])
                    questions.extend(qs)

        return {
            'success': True,
            'pipeline_type': 'pdf',
            'questions': questions,
            'output_path': str(output_file) if output_file.exists() else None,
            'results': []
        }

    def _extract_questions_from_result(self, result: Dict[str, Any]) -> List[str]:
        """從結果中提取問題"""
        questions = []

        # 從 augmented_queries_path 讀取
        output_path = result.get('augmented_queries_path')
        if output_path and Path(output_path).exists():
            with open(output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    qs = item.get('questions', [])
                    questions.extend(qs)

        return questions

    def cleanup(self):
        """清理臨時目錄"""
        if self.temp_dir and self.temp_dir.exists():
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                print(f"清理臨時目錄失敗: {e}")


# 全域處理器實例
processor = FileProcessor()


def process_uploaded_files(files: List[Any], model_name: str, temperature: float, max_tokens: int, progress=gr.Progress()) -> Tuple[str, str, str]:
    """
    處理上傳的多個檔案

    Returns:
        (狀態訊息, 問題文字, 結果 JSON)
    """
    if not files or all(f is None for f in files):
        return "❌ 請上傳至少一個檔案", "", ""

    # 過濾掉 None 值
    files = [f for f in files if f is not None]

    try:
        # 更新 model 配置
        processor.update_model_config(model_name, temperature, max_tokens)

        # 處理檔案
        result = processor.process_files(files, progress)

        if not result.get('success'):
            error_msg = f"❌ 處理失敗\n\n錯誤: {result.get('error', '未知錯誤')}"
            if 'traceback' in result:
                error_msg += f"\n\n詳細錯誤:\n{result['traceback']}"
            return error_msg, "", ""

        # 格式化狀態訊息
        status = "✅ 處理成功!\n\n"
        status += f"📊 Pipeline 類型: {result.get('pipeline_type', 'unknown').upper()}\n"

        if 'file_count' in result:
            status += f"📁 處理檔案數: {result.get('file_count', 0)}\n"

        if 'total_count' in result:
            status += f"📝 處理資料數: {result.get('total_count', 0)}\n"

        questions = result.get('questions', [])
        status += f"❓ 生成問題數: {len(questions)}\n"

        if result.get('output_path'):
            status += f"\n💾 輸出檔案: {result.get('output_path')}\n"

        status += f"\n⏰ 完成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        # 格式化問題
        if questions:
            questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
        else:
            questions_text = "未生成任何問題"

        # 格式化結果 JSON
        result_json = json.dumps(result, ensure_ascii=False, indent=2)

        return status, questions_text, result_json

    except Exception as e:
        import traceback
        error_msg = f"❌ 處理過程中發生錯誤\n\n"
        error_msg += f"錯誤: {str(e)}\n\n"
        error_msg += f"詳細錯誤:\n{traceback.format_exc()}"
        return error_msg, "", ""


def update_model_selection(model_name: str, temperature: float, max_tokens: int) -> str:
    """更新選擇的 model"""
    try:
        processor.update_model_config(model_name, temperature, max_tokens)
        return f"✅ 已選擇 Model: {model_name}\n🌡️ Temperature: {temperature}\n📊 Max Tokens: {max_tokens}"
    except Exception as e:
        return f"❌ 更新 Model 失敗: {str(e)}"


def create_ui():
    """創建 Gradio UI"""

    with gr.Blocks(title="Auto-Gen MultiModel V2") as demo:
        gr.Markdown("# 🚀 Auto-Gen MultiModel V2")

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### ⚙️ Model 選擇")
                model_dropdown = gr.Radio(
                    choices=["mistralai3", "gpt-oss", "gemma3"],
                    value="mistralai3",
                    label="AutoGen Model",
                    info="選擇用於生成問題的 LLM 模型"
                )

                with gr.Row():
                    temperature_slider = gr.Slider(
                        minimum=0.0,
                        maximum=2.0,
                        value=0.7,
                        step=0.1,
                        label="Temperature",
                        info="控制生成的隨機性 (0.0 = 確定性, 2.0 = 高隨機性)"
                    )

                    max_tokens_slider = gr.Slider(
                        minimum=512,
                        maximum=8192,
                        value=4096,
                        step=512,
                        label="Max Tokens",
                        info="生成的最大 token 數量"
                    )


        gr.Markdown("---")

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 📤 上傳檔案")
                file_upload = gr.File(
                    label="選擇多個檔案（可拖曳資料夾）",
                    file_count="multiple",
                    file_types=[
                        ".xlsx", ".xls", ".xlsm", ".xlsb",  # Excel
                        ".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".webp",  # 圖片
                        ".pdf"  # PDF
                    ],
                    elem_classes="file-upload"
                )

                process_btn = gr.Button(
                    "🚀 開始處理",
                    variant="primary",
                    size="lg",
                    scale=1
                )

                status_output = gr.Textbox(
                    label="📊 處理狀態",
                    lines=10,
                    interactive=False,
                    elem_classes="status-box"
                )

        gr.Markdown("---")

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### ❓ 生成的問題")
                questions_output = gr.Textbox(
                    label="Questions",
                    lines=25,
                    interactive=False,
                    placeholder="處理完成後，生成的問題將顯示在這裡..."
                )

            with gr.Column(scale=1):
                gr.Markdown("### 📋 詳細結果 (JSON)")
                result_json = gr.Textbox(
                    label="Result JSON",
                    lines=25,
                    interactive=False,
                    placeholder="處理結果的詳細 JSON 將顯示在這裡..."
                )

        # 綁定處理函數
        process_btn.click(
            fn=process_uploaded_files,
            inputs=[file_upload, model_dropdown, temperature_slider, max_tokens_slider],
            outputs=[status_output, questions_output, result_json]
        )

    return demo


def main():
    """啟動 Web UI V2"""
    # 建立必要的輸出目錄
    Path('results/web_ui_v2').mkdir(parents=True, exist_ok=True)

    # 載入預設配置
    processor.load_config()

    demo = create_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7861,
        share=False,
        show_error=True
    )


if __name__ == "__main__":
    main()
