#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主入口程式 - 根據配置文件自動選擇對應的 Pipeline
支援的文件類型:
    - Excel (.xlsx, .xls): 使用 excel_pipeline
    - 圖片 (.png, .jpg, .jpeg): 使用 img_pipeline
    - PDF (.pdf): 先轉換為圖片後使用 img_pipeline
"""

import sys
from pathlib import Path

# 將專案根目錄加入 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import argparse
import yaml
from typing import Dict, Any, Optional
import tempfile

# 導入 pipeline
from core.excel_pipeline import run as excel_run
from core.ocr import ocr
from core.gen_ques_for_img import gen_ques
from lib.utils.pdf_to_image import PDFToImageConverter


def load_config(config_path: Path) -> Dict[str, Any]:
    """
    載入配置文件

    Args:
        config_path: 配置文件路徑

    Returns:
        配置字典
    """
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    return config


def get_file_type(file_path: Path) -> str:
    """
    判斷文件類型（支援單檔或目錄）

    Args:
        file_path: 文件路徑或目錄路徑

    Returns:
        文件類型: 'excel', 'image', 'pdf', 'directory', 或 'unknown'
    """
    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    # 如果是目錄，返回 directory
    if file_path.is_dir():
        return 'directory'

    suffix = file_path.suffix.lower()

    # Excel 文件
    if suffix in ['.xlsx', '.xls', '.xlsm', '.xlsb']:
        return 'excel'

    # 圖片文件
    elif suffix in ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp']:
        return 'image'

    # PDF 文件
    elif suffix == '.pdf':
        return 'pdf'

    else:
        return 'unknown'


def determine_pipeline_type(config: Dict[str, Any]) -> str:
    """
    根據配置決定 Pipeline 類型

    Args:
        config: 配置字典

    Returns:
        Pipeline 類型: 'excel', 'image', 'pdf'

    Raises:
        ValueError: 當目錄中包含多種文件類型時
    """
    pipeline_type = config.get('pipeline_type', 'auto')

    if pipeline_type == 'auto':
        # 自動檢測：根據輸入文件副檔名判斷
        input_path = Path(config['input'])
        file_type = get_file_type(input_path)

        # 如果是目錄，檢查目錄中的檔案類型
        if file_type == 'directory':
            # 定義支援的檔案類型
            excel_extensions = ['.xlsx', '.xls', '.xlsm', '.xlsb']
            image_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp']
            pdf_extensions = ['.pdf']

            # 收集各類型的檔案
            excel_files = [f for f in input_path.iterdir() if f.is_file() and f.suffix.lower() in excel_extensions]
            image_files = [f for f in input_path.iterdir() if f.is_file() and f.suffix.lower() in image_extensions]
            pdf_files = [f for f in input_path.iterdir() if f.is_file() and f.suffix.lower() in pdf_extensions]

            # 統計有幾種檔案類型
            file_types_found = []
            if excel_files:
                file_types_found.append('Excel')
            if image_files:
                file_types_found.append('圖片')
            if pdf_files:
                file_types_found.append('PDF')

            # 檢查是否為混合類型目錄
            if len(file_types_found) > 1:
                raise ValueError(
                    f"錯誤：目錄中包含多種文件類型，只能處理同質目錄\n"
                    f"目錄: {input_path}\n"
                    f"發現的類型: {', '.join(file_types_found)}\n"
                    f"  - Excel 檔案數: {len(excel_files)}\n"
                    f"  - 圖片檔案數: {len(image_files)}\n"
                    f"  - PDF 檔案數: {len(pdf_files)}\n"
                    "請將不同類型的檔案分別放在不同的目錄中"
                )

            # 根據找到的類型返回對應的 pipeline
            if excel_files:
                return 'excel'
            elif image_files:
                return 'image'
            elif pdf_files:
                return 'pdf'
            else:
                raise ValueError(
                    f"目錄中找不到支援的檔案類型: {input_path}\n"
                    "支援的類型:\n"
                    "  - Excel: .xlsx, .xls, .xlsm, .xlsb\n"
                    "  - 圖片: .png, .jpg, .jpeg, .bmp, .gif, .tiff, .webp\n"
                    "  - PDF: .pdf"
                )

        if file_type == 'unknown':
            raise ValueError(
                f"無法識別的文件類型: {input_path.suffix}\n"
                "支援的類型:\n"
                "  - Excel: .xlsx, .xls, .xlsm, .xlsb\n"
                "  - 圖片: .png, .jpg, .jpeg, .bmp, .gif, .tiff, .webp\n"
                "  - PDF: .pdf"
            )

        return file_type
    else:
        # 使用配置中指定的類型
        return pipeline_type


def run_excel_pipeline(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    執行 Excel Pipeline（支援單檔或批次處理）

    Args:
        config: 統一配置字典

    Returns:
        執行結果字典
    """
    print("=" * 80)
    print("執行 Excel Pipeline")
    print("=" * 80)

    input_path = Path(config['input'])
    excel_config = config.get('excel', {})
    metadata = config.get('metadata', {})

    # 判斷是單檔還是目錄
    is_directory = input_path.is_dir()

    # 構建 Excel Pipeline 需要的配置格式
    pipeline_config = {
        'input': {},
        'output': {
            'dir': excel_config.get('output_dir', 'results/excel/')
        },
        'parser': excel_config.get('parser', {}),
        'augmenter': excel_config.get('augmenter', {}),
        'metadata': metadata
    }

    # 根據輸入類型設置不同的參數
    if is_directory:
        # 批次模式：使用 input_dir
        pipeline_config['input']['input_dir'] = str(input_path.resolve())
        print(f"模式: 批次處理")
        print(f"輸入目錄: {input_path}")
    else:
        # 單檔模式：使用 file_path
        pipeline_config['input']['file_path'] = str(input_path.resolve())
        print(f"模式: 單檔處理")
        print(f"輸入檔案: {input_path}")

    # 共同參數
    pipeline_config['input']['skip_parser'] = excel_config.get('skip_parser', False)
    pipeline_config['input']['parsed_data_path'] = excel_config.get('parsed_data_path', 'results/parsed_data.json')

    print("=" * 80)

    # 執行 Excel Pipeline
    result = excel_run(config=pipeline_config)

    return result


def run_pdf_pipeline(config: Dict[str, Any]) -> bool:
    """
    執行 PDF Pipeline (先轉圖片再執行圖片 Pipeline)

    Args:
        config: 統一配置字典

    Returns:
        是否成功
    """
    print("=" * 80)
    print("執行 PDF Pipeline：先轉換為圖片後進行 OCR 和問題生成")
    print("=" * 80)

    input_path = Path(config['input'])
    pdf_config = config.get('pdf', {})
    metadata = config.get('metadata', {})

    # PDF 轉換設定
    conversion_config = pdf_config.get('conversion', {})
    dpi = conversion_config.get('dpi', 200)
    fmt = conversion_config.get('format', 'PNG')
    max_size = conversion_config.get('max_size', 1024)

    # 使用 PDF 轉圖片轉換器
    converter = PDFToImageConverter(dpi=dpi, max_size=max_size, fmt=fmt)

    print("\n" + "=" * 80)
    print("步驟 1: 將 PDF 轉換為圖片")
    print("=" * 80)
    print(f"DPI: {dpi}, 格式: {fmt}, 最大尺寸: {max_size}")

    # 判斷 input_path 是目錄還是檔案
    if input_path.is_dir():
        # 目錄：使用 convert_batch
        print(f"輸入為目錄：{input_path}")
        pdf_images_dir = input_path.parent / f"{input_path.name}_images"
        pdf_images_dir.mkdir(parents=True, exist_ok=True)

        batch_output = converter.convert_batch(
            input_dir=str(input_path),
            output_dir=str(pdf_images_dir)
        )

        if batch_output.total == 0 or batch_output.success == 0:
            print(f"\n錯誤：目錄中沒有找到 PDF 檔案或全部轉換失敗")
            return False

        # 統計結果
        total_pages = sum(r.total_pages for r in batch_output.results if r.status == 'success')
        total_images = sum(len(r.image_paths) for r in batch_output.results if r.status == 'success')

        print(f"\n✓ 批次 PDF 轉圖片完成")
        print(f"  - 成功檔案數：{batch_output.success}/{batch_output.total}")
        print(f"  - 總頁數：{total_pages}")
        print(f"  - 總圖片數：{total_images}")
        print(f"  - 輸出目錄：{pdf_images_dir}")

    else:
        # 單一檔案：使用 convert
        print(f"輸入為單一檔案：{input_path}")
        pdf_images_dir = input_path.parent / f"{input_path.stem}_images"
        pdf_images_dir.mkdir(parents=True, exist_ok=True)

        result = converter.convert(
            pdf_path=str(input_path),
            output_dir=str(pdf_images_dir),
            filename_prefix=input_path.stem
        )

        if result.status != 'success':
            print(f"\n錯誤：PDF 轉圖片失敗 - {result.error}")
            return False

        print(f"\n✓ PDF 轉圖片完成")
        print(f"  - 總頁數：{result.total_pages}")
        print(f"  - 圖片數：{len(result.image_paths)}")
        print(f"  - 輸出目錄：{result.output_dir}")

    # 執行圖片 Pipeline
    print("\n" + "=" * 80)
    print("步驟 2: 對轉換後的圖片執行 OCR 和問題生成")
    print("=" * 80)

    # 使用 PDF 配置中的 OCR 和 gen_ques 設定
    ocr_config = pdf_config.get('ocr', {})
    gen_ques_config = pdf_config.get('gen_ques', {})
    ocr_only = pdf_config.get('ocr_only', False)

    # 執行圖片 Pipeline
    success = _run_image_ocr_and_gen(
        input_dir=pdf_images_dir,
        ocr_config=ocr_config,
        gen_ques_config=gen_ques_config,
        ocr_only=ocr_only,
        metadata=metadata
    )

    if success:
        print("\n" + "=" * 80)
        print("PDF Pipeline 執行完成！")
        print("=" * 80)

    return success


def run_image_pipeline(config: Dict[str, Any]) -> bool:
    """
    執行圖片 Pipeline

    Args:
        config: 統一配置字典

    Returns:
        是否成功
    """
    print("=" * 80)
    print("執行圖片 Pipeline")
    print("=" * 80)

    input_path = Path(config['input'])
    image_config = config.get('image', {})
    metadata = config.get('metadata', {})

    # 取得 OCR 和 gen_ques 配置
    ocr_config = image_config.get('ocr', {})
    gen_ques_config = image_config.get('gen_ques', {})
    ocr_only = image_config.get('ocr_only', False)

    # 判斷輸入是文件還是目錄
    if input_path.is_file():
        # 單一圖片文件：使用文件所在目錄
        input_dir = input_path.parent
    else:
        # 目錄：直接使用
        input_dir = input_path

    # 執行圖片 Pipeline
    success = _run_image_ocr_and_gen(
        input_dir=input_dir,
        ocr_config=ocr_config,
        gen_ques_config=gen_ques_config,
        ocr_only=ocr_only,
        metadata=metadata
    )

    if success:
        print("\n" + "=" * 80)
        print("圖片 Pipeline 執行完成！")
        print("=" * 80)

    return success


def _run_image_ocr_and_gen(
    input_dir: Path,
    ocr_config: Dict[str, Any],
    gen_ques_config: Dict[str, Any],
    ocr_only: bool = False,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    執行圖片 OCR 和問題生成的內部函數

    Args:
        input_dir: 輸入圖片目錄
        ocr_config: OCR 配置
        gen_ques_config: 生成問題配置
        ocr_only: 是否只執行 OCR
        metadata: 元數據

    Returns:
        是否成功
    """

    # 準備 OCR 配置
    ocr_cfg = {
        'input_dir': str(input_dir),
        'output_dir': ocr_config.get('output_dir', './results/ocr/'),
        'engine': ocr_config.get('engine', 'paddle'),
        'mode': ocr_config.get('mode', 'vllm'),
        'recursive': ocr_config.get('recursive', True),
        'metadata': metadata or {}
    }

    # 添加對應模式的配置
    mode = ocr_cfg['mode']
    if mode in ocr_config:
        ocr_cfg[mode] = ocr_config[mode]

    # 建立臨時 OCR 配置文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False, encoding='utf-8') as tmp_ocr:
        yaml.dump(ocr_cfg, tmp_ocr, allow_unicode=True)
        tmp_ocr_path = tmp_ocr.name

    try:
        # 執行 OCR
        print("\n" + "=" * 80)
        print("執行 OCR 辨識")
        print("=" * 80)
        print(f"引擎: {ocr_cfg['engine']}, 模式: {ocr_cfg['mode']}")

        batch_result = ocr(config_path=tmp_ocr_path)

        if not batch_result:
            print("\n錯誤：OCR 執行失敗")
            return False

        print(f"\n✓ OCR 完成")
        print(f"  - 總圖片數：{batch_result.total_images}")
        print(f"  - 成功：{batch_result.success}")
        print(f"  - 失敗：{batch_result.failed}")
        if batch_result.output_file:
            print(f"  - 輸出文件：{batch_result.output_file}")

        # 執行生成問題
        if not ocr_only:
            # 準備 gen_ques 配置
            gen_cfg = {
                'input': str(batch_result.output_file) if batch_result.output_file else '',
                'output_dir': gen_ques_config.get('output_dir', 'results/ocr/'),
                'mode': gen_ques_config.get('mode', 'vllm'),
                'prompt_name': gen_ques_config.get('prompt_name', 'default'),
                'verify_connection': gen_ques_config.get('verify_connection', False),
                'metadata': metadata or {}
            }

            # 添加對應模式的配置
            mode = gen_cfg['mode']
            if mode in gen_ques_config:
                gen_cfg[mode] = gen_ques_config[mode]

            # 建立臨時 gen_ques 配置文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False, encoding='utf-8') as tmp_gen:
                yaml.dump(gen_cfg, tmp_gen, allow_unicode=True)
                tmp_gen_path = tmp_gen.name

            try:
                print("\n" + "=" * 80)
                print("生成問題")
                print("=" * 80)
                print(f"模式: {gen_cfg['mode']}, Prompt: {gen_cfg['prompt_name']}")

                gen_ques(config_path=tmp_gen_path)

                print(f"\n✓ 生成問題完成")
            finally:
                # 清理臨時配置文件
                Path(tmp_gen_path).unlink(missing_ok=True)

        return True

    finally:
        # 清理臨時配置文件
        Path(tmp_ocr_path).unlink(missing_ok=True)


def main():
    """主程式入口：根據配置文件執行對應的 Pipeline"""
    parser = argparse.ArgumentParser(
        description="根據統一配置文件執行對應的 Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例：
    # 使用統一配置文件（自動檢測文件類型）
    python core/main.py --config configs/unified_pipeline.example.yml

    # 覆蓋配置中的輸入文件
    python core/main.py --config configs/unified_pipeline.example.yml --input data/custom.xlsx

    # 強制指定 Pipeline 類型（覆蓋配置）
    python core/main.py --config configs/unified_pipeline.example.yml --type pdf

配置文件結構說明：
    - 使用 YAML 格式
    - 支援 Excel、Image、PDF 三種 Pipeline
    - 可包含 metadata（元數據）
    - 詳見 configs/unified_pipeline.example.yml
        """
    )

    parser.add_argument(
        "--config", "-c",
        type=str,
        required=True,
        help="統一配置檔路徑（YAML 格式）"
    )

    parser.add_argument(
        "--input", "-i",
        type=str,
        help="輸入文件路徑（覆蓋配置文件中的設定）"
    )

    parser.add_argument(
        "--type", "-t",
        type=str,
        choices=['excel', 'image', 'pdf', 'auto'],
        help="強制指定 Pipeline 類型（覆蓋配置文件中的設定）"
    )

    args = parser.parse_args()

    # 載入配置
    config_path = Path(args.config)
    print(f"載入配置文件: {config_path}")
    config = load_config(config_path)

    # 覆蓋配置（如果命令列有指定）
    if args.input:
        config['input'] = args.input
        print(f"覆蓋輸入文件: {args.input}")

    if args.type:
        config['pipeline_type'] = args.type
        print(f"覆蓋 Pipeline 類型: {args.type}")

    # 檢查是否有輸入文件
    if 'input' not in config:
        print("錯誤：配置文件中缺少 'input' 欄位，且未通過命令列指定")
        sys.exit(1)

    # 取得輸入文件路徑
    input_path = Path(config['input'])

    # 判斷 Pipeline 類型
    try:
        pipeline_type = determine_pipeline_type(config)
    except ValueError as e:
        print(f"錯誤：{e}")
        sys.exit(1)

    # 顯示元數據（如果有）
    metadata = config.get('metadata', {})
    if metadata:
        print("\n" + "=" * 80)
        print("元數據 (Metadata)")
        print("=" * 80)
        for key, value in metadata.items():
            print(f"  {key}: {value}")

    print("\n" + "=" * 80)
    print(f"輸入文件: {input_path}")
    print(f"Pipeline 類型: {pipeline_type}")
    print("=" * 80)

    # 根據 Pipeline 類型執行對應的處理
    try:
        if pipeline_type == 'excel':
            result = run_excel_pipeline(config)

            # 顯示結果
            if result.get("success"):
                print(f"\n✓ Excel Pipeline 執行成功")

                # 如果是批次模式，顯示檔案數量
                if result.get('batch_mode'):
                    print(f"  - 處理模式: 批次處理")
                    print(f"  - 處理檔案數: {result.get('file_count', 'N/A')}")
                else:
                    print(f"  - 處理模式: 單檔處理")

                print(f"  - 處理數據數: {result.get('total_count', 'N/A')}")
                print(f"  - Parser 輸出: {result.get('parsed_data_path', 'N/A')}")
                print(f"  - Augmenter 輸出: {result.get('augmented_queries_path', 'N/A')}")
            else:
                print(f"\n✗ 執行失敗: {result.get('error', '未知錯誤')}")
                sys.exit(1)

        elif pipeline_type == 'image':
            success = run_image_pipeline(config)

            if not success:
                sys.exit(1)

        elif pipeline_type == 'pdf':
            success = run_pdf_pipeline(config)

            if not success:
                sys.exit(1)

        else:
            print(f"錯誤：不支援的 Pipeline 類型 - {pipeline_type}")
            sys.exit(1)

    except Exception as e:
        print(f"\n錯誤：執行過程中發生異常")
        print(f"  {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
