# Excel Parser CLI

將 Excel 檔案解析為 JSON 格式的命令列工具。

## 功能特色

- 支援解析單一檔案或整個目錄
- 輸出 JSON 格式，包含每個儲存格的詳細資訊
- 可選擇是否包含空白儲存格
- 支援摘要模式和安靜模式
- 自動處理中文編碼

## 安裝依賴

```bash
pip install openpyxl
```

## 使用方式

### 查看幫助

```bash
python excel_parser.py --help
```

### 基本使用

#### 1. 解析單一檔案（使用預設檔案）

```bash
python excel_parser.py
```

預設會解析 `表12-1.xlsx`，輸出到 `parsed_data/表12-1.json`

#### 2. 解析指定的單一檔案

```bash
python excel_parser.py --file 表12-2.xlsx
```

或使用短參數：

```bash
python excel_parser.py -f 表12-2.xlsx
```

#### 3. 解析整個目錄（使用預設目錄）

```bash
python excel_parser.py --mode dir
```

預設會解析 `raw_data/一般服務/` 目錄中的所有 Excel 檔案

#### 4. 解析指定目錄

```bash
python excel_parser.py --mode dir --dir raw_data/專款項目
```

或使用短參數：

```bash
python excel_parser.py --mode dir -d raw_data/專款項目
```

### 進階選項

#### 指定輸出路徑

```bash
# 單一檔案
python excel_parser.py -f 表12-1.xlsx -o my_output.json

# 目錄模式
python excel_parser.py --mode dir -d raw_data/一般服務 -o my_parsed_data
```

#### 包含空白儲存格

```bash
python excel_parser.py -f 表12-1.xlsx --include-empty
```

#### 僅顯示摘要（不儲存完整 JSON）

```bash
python excel_parser.py -f 表12-1.xlsx --summary-only
```

#### 安靜模式（減少輸出訊息）

```bash
python excel_parser.py -f 表12-1.xlsx -q
```

### 組合使用

```bash
# 解析目錄，包含空白儲存格，輸出到指定目錄
python excel_parser.py --mode dir -d raw_data/一般服務 -o output --include-empty

# 快速查看檔案摘要
python excel_parser.py -f 表12-1.xlsx --summary-only -q
```

## 輸出格式

### 單一檔案輸出範例

```json
{
  "file_name": "表12-1.xlsx",
  "file_path": "C:\\path\\to\\表12-1.xlsx",
  "sheets": [
    {
      "sheet_name": "Sheet1",
      "cell_count": 150
    }
  ],
  "cells": [
    {
      "sheet_name": "Sheet1",
      "row_name": "1",
      "col_name": "A",
      "cell_address": "A1",
      "content": "標題"
    },
    {
      "sheet_name": "Sheet1",
      "row_name": "1",
      "col_name": "B",
      "cell_address": "B1",
      "content": "數值"
    }
  ],
  "total_cells": 150
}
```

### 目錄模式輸出

解析目錄時會產生：

1. **個別 JSON 檔案**：每個 Excel 檔案對應一個 JSON
   - `parsed_data/表12-1.json`
   - `parsed_data/表12-2.json`
   - ...

2. **總覽檔案**：`parsed_data/summary.json`
```json
{
  "total_files": 10,
  "files": [
    {
      "file_name": "表12-1.xlsx",
      "sheets": 1,
      "total_cells": 150
    },
    {
      "file_name": "表12-2.xlsx",
      "sheets": 2,
      "total_cells": 200
    }
  ]
}
```

## 命令列參數

| 參數 | 短參數 | 預設值 | 說明 |
|------|--------|--------|------|
| `--mode` | - | `file` | 處理模式：`file` 或 `dir` |
| `--file` | `-f` | `表12-1.xlsx` | 要解析的 Excel 檔案路徑 |
| `--dir` | `-d` | `raw_data/一般服務` | 要解析的目錄路徑 |
| `--output` | `-o` | `parsed_data/` | 輸出檔案或目錄路徑 |
| `--include-empty` | - | `False` | 包含空白儲存格 |
| `--summary-only` | - | `False` | 僅顯示摘要，不儲存 JSON |
| `--quiet` | `-q` | `False` | 安靜模式 |

## 支援的檔案格式

- `.xlsx` - Excel 2007+ 格式
- `.xlsm` - 含巨集的 Excel 檔案
- `.xltx` - Excel 範本
- `.xltm` - 含巨集的 Excel 範本

## 錯誤處理

程式會進行以下檢查：

1. ✓ 檔案/目錄是否存在
2. ✓ 檔案格式是否支援
3. ✓ 檔案是否可讀取
4. ✓ 輸出目錄是否可建立

發生錯誤時會顯示清楚的錯誤訊息並返回非零的退出碼。

## 常見使用場景

### 場景 1：批次處理所有報表

```bash
python excel_parser.py --mode dir -d raw_data/一般服務 -o results
```

### 場景 2：快速檢視檔案內容

```bash
python excel_parser.py -f 表12-1.xlsx --summary-only
```

輸出範例：
```
======================================================================
Excel Parser
======================================================================

解析檔案: 表12-1.xlsx
  檔案名稱: 表12-1.xlsx
  工作表數: 1
    - Sheet1: 150 個儲存格
  總儲存格數: 150

======================================================================
✓ 完成！
======================================================================
```

### 場景 3：匯出完整資料（包含空格）

```bash
python excel_parser.py -f 表12-1.xlsx --include-empty -o full_data.json
```

### 場景 4：自動化腳本使用（安靜模式）

```bash
python excel_parser.py -f 表12-1.xlsx -o output.json -q
echo "處理完成，退出碼: $?"
```

## 作為 Python 模組使用

也可以在其他 Python 程式中匯入使用：

```python
from excel_parser import parse_excel_file, parse_excel_directory

# 解析單一檔案
result = parse_excel_file("表12-1.xlsx")
print(f"總共 {result['total_cells']} 個儲存格")

# 解析目錄
results = parse_excel_directory("raw_data/一般服務", output_dir="parsed_data")
print(f"解析了 {len(results)} 個檔案")
```

## 疑難排解

### 問題：找不到檔案

```
錯誤：檔案不存在 - 表12-1.xlsx
```

**解決方法**：
- 確認檔案路徑是否正確
- 使用絕對路徑或相對於當前目錄的路徑

### 問題：編碼錯誤

**解決方法**：
- 程式已自動處理 UTF-8 編碼
- 確保終端機支援 UTF-8 顯示

### 問題：記憶體不足

處理大型 Excel 檔案時可能遇到記憶體問題。

**解決方法**：
- 分批處理檔案
- 不使用 `--include-empty` 選項

## 授權

本工具為專案內部使用。
