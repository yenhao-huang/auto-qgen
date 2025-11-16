# Excel Parser LLM 轉換為 AugmenterInput 使用說明

## 概述

`ExcelParserLLM.transform_to_augmenterInput()` 方法可以將 Excel Parser LLM 的輸出轉換為 Augmenter 可用的輸入格式。

## 方法位置

```python
from utils.parser.excel_parser_llm import ExcelParserLLM
```

## 使用方式

### 基本用法

```python
import json
from utils.parser.excel_parser_llm import ExcelParserLLM

# 1. 讀取 Excel Parser LLM 的輸出
with open('data/parsed_data/youtube_100_records.json', 'r', encoding='utf-8') as f:
    parsed_excel = json.load(f)

# 2. 轉換所有儲存格
augmenter_inputs = ExcelParserLLM.transform_to_augmenterInput(parsed_excel)

# 3. 儲存結果
with open('output.json', 'w', encoding='utf-8') as f:
    json.dump(augmenter_inputs, f, ensure_ascii=False, indent=2)
```

### 只轉換特定儲存格

```python
# 只轉換第 7 個儲存格（索引從 0 開始）
single_cell = ExcelParserLLM.transform_to_augmenterInput(parsed_excel, cell_index=6)
```

## 輸入格式

Excel Parser LLM 的輸出格式：

```json
{
  "file_name": "youtube_100_records.xlsx",
  "title": "YouTube 影音資料紀錄",
  "x-axis": "欄位標題（影片屬性）",
  "y-axis": "影片紀錄編號（video_id）",
  "cells": [
    {
      "x-axis id": "E",
      "y-axis id": "7",
      "x-axis id 意思": "觀看次數",
      "y-axis id 意思": "第七筆影片紀錄（Cooking Pasta）",
      "值": "1754397"
    }
  ]
}
```

## 輸出格式

轉換後的 AugmenterInput 格式：

```json
{
  "keyword": {
    "table_title": "YouTube 影音資料紀錄",
    "table's x-axis": "欄位標題（影片屬性）",
    "table's y-axis": "影片紀錄編號（video_id）",
    "cell's x-axis id 意思": "觀看次數",
    "cell's y-axis id 意思": "第七筆影片紀錄（Cooking Pasta）",
    "值": "1754397"
  },
  "ground_truth": {
    "file_name": "youtube_100_records.xlsx",
    "item_id": [7]
  },
  "metadata": {
    "x-axis id": "E",
    "y-axis id": "7",
    "source": "excel_parser_llm"
  }
}
```

## 完整工作流程

### 步驟 1：使用 Excel Parser LLM 解析 Excel

```bash
python utils/parser/excel_parser_llm.py \
  --file data/vedio/youtube_100_records.xlsx \
  --vllm-url https://openrouter.ai \
  --model google/gemini-2.0-flash-exp:free \
  --use-openrouter \
  --api-key YOUR_API_KEY
```

輸出：`data/parsed_data/youtube_100_records.json`

### 步驟 2：轉換為 AugmenterInput 格式

```python
import json
from utils.parser.excel_parser_llm import ExcelParserLLM

# 讀取 Parser 輸出
with open('data/parsed_data/youtube_100_records.json', 'r', encoding='utf-8') as f:
    parsed_data = json.load(f)

# 轉換格式
augmenter_inputs = ExcelParserLLM.transform_to_augmenterInput(parsed_data)

# 儲存轉換結果
with open('data/augmenter_input/youtube_100_records.json', 'w', encoding='utf-8') as f:
    json.dump(augmenter_inputs, f, ensure_ascii=False, indent=2)
```

### 步驟 3：使用 LLM Augmenter 生成查詢

```bash
python utils/augmenter/llm_augmenter.py \
  -i data/augmenter_input/youtube_100_records.json \
  -o results/augmenter/augmented_queries.json \
  --vllm-url https://openrouter.ai \
  --model google/gemini-2.0-flash-exp:free \
  --use-openrouter \
  --api-key YOUR_API_KEY
```

## 範例腳本

執行範例腳本查看完整流程：

```bash
python example_transform_excel_to_augmenter.py
```

## 注意事項

1. **item_id 轉換**：`y-axis id` 會被轉換為整數列表。如果無法轉換為整數，則使用 `[0]` 作為預設值。

2. **metadata**：轉換後的資料會在 `metadata` 中保留原始的 `x-axis id` 和 `y-axis id`，並標記 `source` 為 `"excel_parser_llm"`。

3. **檔案名稱**：`file_name` 會從 Excel Parser LLM 的輸出中提取，保持原樣。

## API 參考

### `ExcelParserLLM.transform_to_augmenterInput()`

**參數：**
- `excel_parser_output` (Dict[str, Any]): Excel Parser LLM 的輸出 JSON
- `cell_index` (Optional[int]): 要轉換的儲存格索引（預設：None）
  - `None`: 轉換所有儲存格
  - 整數: 只轉換該索引的儲存格（從 0 開始）

**回傳：**
- `List[Dict[str, Any]]`: 轉換後的 AugmenterInput 格式列表

**異常：**
- `IndexError`: 當 `cell_index` 超出範圍時
