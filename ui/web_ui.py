#!/usr/bin/env python3
"""
Web UI for Auto-Gen MultiModel
提供簡單的介面上傳檔案並顯示生成的問題
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import gradio as gr
import json
import tempfile
import yaml
from typing import List, Dict, Any, Tuple, Union
from datetime import datetime

from core.excel_pipeline import run as excel_run
from core.ocr import ocr
from core.gen_ques_for_img import gen_ques
from lib.utils.pdf_to_image import PDFToImageConverter


def get_file_type(file_path: Path) -> str:
    """判斷文件類型"""
    suffix = file_path.suffix.lower()

    if suffix in ['.xlsx', '.xls', '.xlsm', '.xlsb']:
        return 'excel'
    elif suffix in ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp']:
        return 'image'
    elif suffix == '.pdf':
        return 'pdf'
    else:
        return 'unknown'


def process_excel_file(file_path: str, config: Dict[str, Any]) -> List[str]:
    """處理 Excel 檔案並返回生成的問題"""
    input_path = Path(file_path)

    # 構建 Excel Pipeline 配置
    pipeline_config = {
        'input': {
            'file_path': str(input_path.resolve()),
            'skip_parser': False,
            'parsed_data_path': 'results/web_ui/parsed_data.json'
        },
        'output': {
            'dir': 'results/web_ui/excel/'
        },
        'parser': config.get('excel', {}).get('parser', {}),
        'augmenter': config.get('excel', {}).get('augmenter', {}),
        'metadata': config.get('metadata', {})
    }

    result = excel_run(config=pipeline_config)

    if not result.get("success"):
        raise Exception(f"Excel 處理失敗: {result.get('error', '未知錯誤')}")

    # 讀取生成的問題
    augmented_path = result.get('augmented_queries_path')
    if augmented_path and Path(augmented_path).exists():
        with open(augmented_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # 收集所有問題
            all_questions = []
            for item in data:
                questions = item.get('questions', [])
                all_questions.extend(questions)
            return all_questions

    return []


def process_image_file(file_path: str, config: Dict[str, Any]) -> List[str]:
    """處理圖片檔案並返回生成的問題"""
    input_path = Path(file_path)
    input_dir = input_path.parent

    # OCR 配置
    ocr_config = config.get('image', {}).get('ocr', {})
    gen_ques_config = config.get('image', {}).get('gen_ques', {})

    ocr_cfg = {
        'input_dir': str(input_dir),
        'output_dir': './results/web_ui/ocr/',
        'engine': ocr_config.get('engine', 'paddle'),
        'mode': ocr_config.get('mode', 'vllm'),
        'recursive': False,
        'metadata': config.get('metadata', {})
    }

    mode = ocr_cfg['mode']
    if mode in ocr_config:
        ocr_cfg[mode] = ocr_config[mode]

    # 建立臨時 OCR 配置文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False, encoding='utf-8') as tmp_ocr:
        yaml.dump(ocr_cfg, tmp_ocr, allow_unicode=True)
        tmp_ocr_path = tmp_ocr.name

    try:
        # 執行 OCR
        batch_result = ocr(config_path=tmp_ocr_path)

        if not batch_result or not batch_result.output_file:
            raise Exception("OCR 執行失敗")

        # 執行問題生成
        gen_cfg = {
            'input': str(batch_result.output_file),
            'output_dir': 'results/web_ui/ocr/',
            'mode': gen_ques_config.get('mode', 'vllm'),
            'prompt_name': gen_ques_config.get('prompt_name', 'default'),
            'verify_connection': False,
            'metadata': config.get('metadata', {})
        }

        mode = gen_cfg['mode']
        if mode in gen_ques_config:
            gen_cfg[mode] = gen_ques_config[mode]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False, encoding='utf-8') as tmp_gen:
            yaml.dump(gen_cfg, tmp_gen, allow_unicode=True)
            tmp_gen_path = tmp_gen.name

        try:
            gen_ques(config_path=tmp_gen_path)

            # 讀取生成的問題
            output_path = Path(gen_cfg['output_dir']) / "augmented_queries.json"
            if output_path.exists():
                with open(output_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    all_questions = []
                    for item in data:
                        questions = item.get('questions', [])
                        all_questions.extend(questions)
                    return all_questions
        finally:
            Path(tmp_gen_path).unlink(missing_ok=True)
    finally:
        Path(tmp_ocr_path).unlink(missing_ok=True)

    return []


def process_pdf_file(file_path: str, config: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """處理 PDF 檔案並返回生成的問題和圖片路徑列表"""
    input_path = Path(file_path)
    pdf_config = config.get('pdf', {})

    # PDF 轉圖片
    conversion_config = pdf_config.get('conversion', {})
    dpi = conversion_config.get('dpi', 200)
    fmt = conversion_config.get('format', 'PNG')
    max_size = conversion_config.get('max_size', 1024)

    pdf_images_dir = Path('./results/web_ui/pdf_images')
    pdf_images_dir.mkdir(parents=True, exist_ok=True)

    converter = PDFToImageConverter(dpi=dpi, max_size=max_size, fmt=fmt)
    result = converter.convert(
        pdf_path=str(input_path),
        output_dir=str(pdf_images_dir),
        filename_prefix=input_path.stem
    )

    if result.status != 'success':
        raise Exception(f"PDF 轉圖片失敗: {result.error}")

    # 保存圖片路徑列表
    pdf_image_paths = result.image_paths

    # 對轉換後的圖片執行 OCR 和問題生成
    ocr_config = pdf_config.get('ocr', {})
    gen_ques_config = pdf_config.get('gen_ques', {})

    ocr_cfg = {
        'input_dir': str(pdf_images_dir),
        'output_dir': './results/web_ui/pdf_ocr/',
        'engine': ocr_config.get('engine', 'paddle'),
        'mode': ocr_config.get('mode', 'vllm'),
        'recursive': True,
        'metadata': config.get('metadata', {})
    }

    mode = ocr_cfg['mode']
    if mode in ocr_config:
        ocr_cfg[mode] = ocr_config[mode]

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False, encoding='utf-8') as tmp_ocr:
        yaml.dump(ocr_cfg, tmp_ocr, allow_unicode=True)
        tmp_ocr_path = tmp_ocr.name

    try:
        batch_result = ocr(config_path=tmp_ocr_path)

        if not batch_result or not batch_result.output_file:
            raise Exception("OCR 執行失敗")

        gen_cfg = {
            'input': str(batch_result.output_file),
            'output_dir': 'results/web_ui/pdf_ocr/',
            'mode': gen_ques_config.get('mode', 'vllm'),
            'prompt_name': gen_ques_config.get('prompt_name', 'default'),
            'verify_connection': False,
            'metadata': config.get('metadata', {})
        }

        mode = gen_cfg['mode']
        if mode in gen_ques_config:
            gen_cfg[mode] = gen_ques_config[mode]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False, encoding='utf-8') as tmp_gen:
            yaml.dump(gen_cfg, tmp_gen, allow_unicode=True)
            tmp_gen_path = tmp_gen.name

        try:
            gen_ques(config_path=tmp_gen_path)

            output_path = Path(gen_cfg['output_dir']) / "augmented_queries.json"
            if output_path.exists():
                with open(output_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    all_questions = []
                    for item in data:
                        questions = item.get('questions', [])
                        all_questions.extend(questions)
                    return all_questions, pdf_image_paths
            return [], pdf_image_paths
        finally:
            Path(tmp_gen_path).unlink(missing_ok=True)
    finally:
        Path(tmp_ocr_path).unlink(missing_ok=True)


def load_default_config() -> Dict[str, Any]:
    """載入預設配置"""
    config_path = Path('configs/unified_pipeline.example.yml')

    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    # 如果沒有配置文件，返回基本配置
    return {
        'metadata': {},
        'excel': {
            'parser': {},
            'augmenter': {}
        },
        'image': {
            'ocr': {
                'engine': 'paddle',
                'mode': 'vllm',
                'vllm': {
                    'base_url': 'http://localhost:8000/v1',
                    'model': 'PaddlePaddle/PaddleOCR-VL'
                }
            },
            'gen_ques': {
                'mode': 'vllm',
                'vllm': {
                    'url': 'http://localhost:8000/v1',
                    'model_name': 'default-model'
                }
            }
        },
        'pdf': {
            'conversion': {
                'dpi': 200,
                'format': 'PNG',
                'max_size': 1024
            },
            'ocr': {
                'engine': 'paddle',
                'mode': 'vllm',
                'vllm': {
                    'base_url': 'http://localhost:8000/v1',
                    'model': 'PaddlePaddle/PaddleOCR-VL'
                }
            },
            'gen_ques': {
                'mode': 'vllm',
                'vllm': {
                    'url': 'http://localhost:8000/v1',
                    'model_name': 'default-model'
                }
            }
        }
    }


def process_file(file) -> Tuple[str, str, Union[List, None], Union[str, None]]:
    """處理上傳的檔案"""
    if file is None:
        return "請上傳檔案", "", None, None

    try:
        file_path = Path(file.name)
        file_type = get_file_type(file_path)

        if file_type == 'unknown':
            return f"不支援的檔案類型: {file_path.suffix}", "", None, None

        # 載入配置
        config = load_default_config()

        # 顯示處理狀態
        status = f"正在處理 {file_type.upper()} 檔案: {file_path.name}...\n"

        image_to_display = None
        gallery_images = None

        # 根據檔案類型處理
        if file_type == 'excel':
            questions = process_excel_file(file.name, config)
        elif file_type == 'image':
            questions = process_image_file(file.name, config)
            # 顯示原始圖片
            image_to_display = file.name
        elif file_type == 'pdf':
            questions, pdf_images = process_pdf_file(file.name, config)
            # 顯示 PDF 轉換後的圖片（使用 gallery）
            if pdf_images:
                gallery_images = pdf_images
        else:
            return f"不支援的檔案類型: {file_type}", "", None, None

        # 格式化輸出
        if questions:
            status += f"\n成功! 共生成 {len(questions)} 個問題\n"
            status += f"處理時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
        else:
            status += "\n警告: 未生成任何問題"
            questions_text = "未生成任何問題"

        return status, questions_text, gallery_images, image_to_display

    except Exception as e:
        error_msg = f"處理失敗: {str(e)}"
        import traceback
        error_msg += f"\n\n詳細錯誤:\n{traceback.format_exc()}"
        return error_msg, "", None, None


def create_ui():
    """創建 Gradio UI"""
    with gr.Blocks(title="Auto-Gen MultiModel", theme=gr.themes.Soft()) as demo:
        gr.Markdown(
            """
            # Auto-Gen MultiModel
            上傳檔案（Excel、圖片或 PDF）自動生成問題
            """
        )

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 上傳檔案")
                file_input = gr.File(
                    label="選擇檔案",
                    file_types=[
                        ".xlsx", ".xls", ".xlsm", ".xlsb",  # Excel
                        ".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".webp",  # 圖片
                        ".pdf"  # PDF
                    ]
                )
                process_btn = gr.Button("開始處理", variant="primary", size="lg")
                status_output = gr.Textbox(
                    label="處理狀態",
                    lines=8,
                    interactive=False
                )

                gr.Markdown("### 預覽")
                # 圖片預覽（單張）
                image_output = gr.Image(
                    label="圖片預覽",
                    visible=True
                )
                # PDF 頁面預覽（多張）
                gallery_output = gr.Gallery(
                    label="PDF 頁面預覽",
                    show_label=True,
                    columns=2,
                    rows=2,
                    height="auto",
                    visible=True
                )

            with gr.Column(scale=1):
                gr.Markdown("### 生成的問題")
                questions_output = gr.Textbox(
                    label="Questions",
                    lines=35,
                    interactive=False,
                    placeholder="處理完成後，生成的問題將顯示在這裡..."
                )

        gr.Markdown(
            """
            ---
            **支援的檔案格式:**
            - Excel: `.xlsx`, `.xls`, `.xlsm`, `.xlsb`
            - 圖片: `.png`, `.jpg`, `.jpeg`, `.bmp`, `.gif`, `.tiff`, `.webp`
            - PDF: `.pdf`
            """
        )

        # 綁定處理函數
        process_btn.click(
            fn=process_file,
            inputs=[file_input],
            outputs=[status_output, questions_output, gallery_output, image_output]
        )

    return demo


def main():
    """啟動 Web UI"""
    # 建立必要的輸出目錄
    Path('results/web_ui').mkdir(parents=True, exist_ok=True)

    demo = create_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )


if __name__ == "__main__":
    main()
