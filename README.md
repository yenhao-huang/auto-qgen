# Auto-Gen MultiModel

自動根據輸入文件類型生成問題的工具，支援多種文件格式。

## 功能

- 圖片 → OCR → 生成問題
- Excel → 解析 → 生成問題
- PDF → 解析 → 生成問題（規劃中）

## 快速開始

### 使用 main.py（推薦）

`main.py` 是統一的入口程式，會自動檢測文件類型並選擇對應的 Pipeline。

#### 基本用法

```bash
# 自動檢測文件類型並處理
python core/main.py --input <文件路徑>
```

#### Excel 文件處理

```bash
# 使用預設配置
python core/main.py --input data/example.xlsx

# 使用自訂配置
python core/main.py --input data/example.xlsx --config configs/excel_augment.example.yml
```

#### 圖片文件處理

```bash
# 完整流程：OCR + 生成問題
python core/main.py --input data/image.png \
  --ocr-config configs/ocr_config.yml \
  --gen-ques-config configs/gen_ques_config.yml
```

### 命令列參數

| 參數 | 簡寫 | 預設值 | 說明 |
|------|------|--------|------|
| `--input` | `-i` | *必填* | 輸入文件路徑（Excel 或圖片） |
| `--type` | `-t` | `auto` | 文件類型：`excel`、`image` 或 `auto`（自動檢測） |
| `--config` | `-c` | `configs/excel_augment.example.yml` | Excel Pipeline 配置檔路徑 |
| `--ocr-config` | - | `configs/ocr_config.yml` | OCR 配置檔路徑（圖片 Pipeline） |
| `--gen-ques-config` | - | `configs/gen_ques_config.yml` | 生成問題配置檔路徑（圖片 Pipeline） |
| `--ocr-only` | - | `False` | 僅執行 OCR，不執行生成問題（圖片 Pipeline） |

### 支援的文件格式

#### Excel 格式
- `.xlsx` - Excel 2007+ 格式
- `.xls` - Excel 97-2003 格式
- `.xlsm` - Excel 啟用巨集的活頁簿
- `.xlsb` - Excel 二進位活頁簿

#### 圖片格式
- `.png` - PNG 圖片
- `.jpg` / `.jpeg` - JPEG 圖片
- `.bmp` - 點陣圖
- `.gif` - GIF 圖片
- `.tiff` - TIFF 圖片
- `.webp` - WebP 圖片

## 配置文件

### Excel Pipeline 配置

參考 [configs/excel_augment.example.yml](configs/excel_augment.example.yml)

### 圖片 Pipeline 配置

1. **OCR 配置**：參考 [configs/ocr_config.yml](configs/ocr_config.yml)
2. **生成問題配置**：參考 [configs/gen_ques_config.yml](configs/gen_ques_config.yml)

## 輸出

- Excel Pipeline：
  - 解析後的數據：`results/parsed_data.json`
  - 生成的問題：`results/augmented_queries.json`
  - LLM 原始回應：`results/augmented_queries_raw_responses.json`

- 圖片 Pipeline：
  - OCR 結果：`results/ocr_results.json`
  - 生成的問題：`results/augmented_queries.json`
  - LLM 原始回應：`results/augmented_queries_raw_responses.json`