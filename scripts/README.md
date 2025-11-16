# Main Pipeline Script 使用說明

## 概述

`main.py` 是一個整合腳本，將 Excel Parser LLM 和 Augmenter 兩個步驟合併為一個完整的處理流程。

**新功能：** 支援 YAML 配置檔案，Parser 和 Augmenter 可以使用不同的 LLM 模型！

## 功能流程

```
Excel 檔案
    ↓
[步驟 1] Excel Parser LLM - 使用指定的 LLM 模型解析 Excel
    ↓
parsed_data.json (中間輸出)
    ↓
[轉換] 轉換為 AugmenterInput 格式
    ↓
[步驟 2] LLM Augmenter - 使用指定的 LLM 模型生成增強查詢
    ↓
augmented_queries.json (最終輸出)
```

## 使用方式

### 方式 1：使用 YAML 配置檔案（推薦）

#### 1.1 建立配置檔案

複製範例配置檔案並修改：

```bash
# 複製範例配置
cp config/config.example.yml config/my_config.yml

# 編輯配置檔案
vim config/my_config.yml
```

**config/my_config.yml 範例：**

```yaml
# 輸入/輸出設定
input:
  file: "data/vedio/youtube_100_records.xlsx"

output:
  dir: "results/youtube_pipeline"
  parsed_data: null
  augmented_queries: null

# Parser LLM 設定（使用本地模型）
parser:
  llm:
    url: "http://192.168.1.79:3472"
    model: "gemma-12b-8bit"
    api_key: null
    use_openrouter: false
    max_retries: 3
    max_tokens: 8000
    temperature: 0.3
    top_p: 0.9

# Augmenter LLM 設定（使用 OpenRouter 免費模型）
augmenter:
  llm:
    url: "https://openrouter.ai"
    model: "google/gemini-2.0-flash-exp:free"
    api_key: "YOUR_API_KEY"
    use_openrouter: true
    max_retries: 3
  prompt_name: "1"

# 執行選項
options:
  skip_parser: false
  quiet: false
```

#### 1.2 執行

```bash
python scripts/main.py --config config/my_config.yml
```

### 方式 2：使用配置檔案 + 命令列參數覆蓋

```bash
# 使用配置檔案，但覆蓋輸入檔案
python scripts/main.py \
  --config config/my_config.yml \
  --file data/other.xlsx

# 使用配置檔案，但更換 Augmenter 的模型
python scripts/main.py \
  --config config/my_config.yml \
  --augmenter-model google/gemini-flash-1.5
```

### 方式 3：純命令列參數（不使用配置檔案）

```bash
python scripts/main.py \
  --file data/vedio/youtube_100_records.xlsx \
  --parser-url http://192.168.1.79:3472 \
  --parser-model gemma-12b-8bit \
  --augmenter-url https://openrouter.ai \
  --augmenter-model google/gemini-2.0-flash-exp:free \
  --augmenter-use-openrouter \
  --augmenter-api-key YOUR_API_KEY
```

## 配置檔案範例

### 範例 1：本地 vLLM

**config/local_vllm.yml**

```yaml
input:
  file: "data/vedio/youtube_100_records.xlsx"

output:
  dir: "results/local_run"

parser:
  llm:
    url: "http://192.168.1.79:3472"
    model: "gemma-12b-8bit"
    api_key: null
    use_openrouter: false
    max_retries: 3

augmenter:
  llm:
    url: "http://192.168.1.79:3472"
    model: "gemma-12b-8bit"
    api_key: null
    use_openrouter: false
    max_retries: 3
  prompt_name: "1"

options:
  skip_parser: false
  quiet: false
```

### 範例 2：混合使用（Parser 用本地，Augmenter 用 OpenRouter）

**config/hybrid.yml**

```yaml
input:
  file: "data/vedio/youtube_100_records.xlsx"

output:
  dir: "results/hybrid_run"

# Parser 使用本地模型（速度較慢但免費）
parser:
  llm:
    url: "http://192.168.1.79:3472"
    model: "gemma-12b-8bit"
    use_openrouter: false
    max_retries: 3

# Augmenter 使用雲端模型（速度快且免費）
augmenter:
  llm:
    url: "https://openrouter.ai"
    model: "google/gemini-2.0-flash-exp:free"
    api_key: "YOUR_API_KEY"
    use_openrouter: true
    max_retries: 3
  prompt_name: "1"
```

### 範例 3：全部使用 OpenRouter

**config/openrouter.yml**

```yaml
input:
  file: "data/vedio/youtube_100_records.xlsx"

output:
  dir: "results/openrouter_run"

parser:
  llm:
    url: "https://openrouter.ai"
    model: "google/gemini-2.0-flash-exp:free"
    api_key: "YOUR_API_KEY"
    use_openrouter: true
    max_retries: 3

augmenter:
  llm:
    url: "https://openrouter.ai"
    model: "google/gemini-2.0-flash-exp:free"
    api_key: "YOUR_API_KEY"
    use_openrouter: true
    max_retries: 3
  prompt_name: "1"
```

## 參數說明

### 配置檔案參數

| 參數 | 說明 | 預設值 |
|------|------|--------|
| `--config`, `-c` | YAML 配置檔案路徑 | None |

### 命令列參數（覆蓋配置檔案）

#### 輸入/輸出參數

| 參數 | 說明 |
|------|------|
| `--file`, `-f` | 要解析的 Excel 檔案路徑 |
| `--output-dir` | 輸出目錄 |
| `--parsed-output` | Parser 輸出檔案路徑 |
| `--augmenter-output` | Augmenter 輸出檔案路徑 |

#### Parser LLM 參數

| 參數 | 說明 |
|------|------|
| `--parser-url` | Parser LLM API URL |
| `--parser-model` | Parser 模型名稱 |
| `--parser-api-key` | Parser API 金鑰 |
| `--parser-use-openrouter` | Parser 使用 OpenRouter API |

#### Augmenter LLM 參數

| 參數 | 說明 |
|------|------|
| `--augmenter-url` | Augmenter LLM API URL |
| `--augmenter-model` | Augmenter 模型名稱 |
| `--augmenter-api-key` | Augmenter API 金鑰 |
| `--augmenter-use-openrouter` | Augmenter 使用 OpenRouter API |
| `--prompt-name` | Prompt 名稱 |

#### 執行選項

| 參數 | 說明 |
|------|------|
| `--skip-parser` | 跳過 Parser 步驟 |
| `--quiet`, `-q` | 安靜模式 |

## 使用場景

### 場景 1：快速測試（使用免費 API）

```bash
python scripts/main.py \
  --config config/openrouter.yml \
  --file data/test.xlsx
```

### 場景 2：省錢方案（Parser 用本地，Augmenter 用免費 API）

Parser 處理較重，使用本地模型節省 API 費用；Augmenter 較輕量，使用免費 API 加速。

```bash
python scripts/main.py --config config/hybrid.yml
```

### 場景 3：重新生成查詢（跳過 Parser）

如果已經有 Parser 的結果，想用不同的 prompt 重新生成查詢：

```bash
python scripts/main.py \
  --config config/my_config.yml \
  --skip-parser \
  --parsed-output results/previous_run/parsed_data.json \
  --prompt-name 2
```

### 場景 4：批次處理多個檔案

```bash
for file in data/*.xlsx; do
  python scripts/main.py \
    --config config/my_config.yml \
    --file "$file" \
    --output-dir "results/$(basename $file .xlsx)"
done
```

## 輸出範例

```bash
$ python scripts/main.py --config config/hybrid.yml

======================================================================
Excel Parser LLM + Augmenter Pipeline
======================================================================
輸入檔案: data/vedio/youtube_100_records.xlsx
輸出目錄: results/hybrid_run
Parser 輸出: results/hybrid_run/parsed_data.json
Augmenter 輸出: results/hybrid_run/augmented_queries.json

Parser LLM 設定:
  URL: http://192.168.1.79:3472
  Model: gemma-12b-8bit
  OpenRouter: False

Augmenter LLM 設定:
  URL: https://openrouter.ai
  Model: google/gemini-2.0-flash-exp:free
  OpenRouter: True
  Prompt: 1
======================================================================

步驟 1/2: 使用 LLM 解析 Excel 檔案
----------------------------------------------------------------------
步驟 0：載入 Excel 檔案 - data/vedio/youtube_100_records.xlsx
  已載入 700 個儲存格

步驟 1：使用 LLM 分析 Excel 內容...
  LLM 分析完成

已儲存結果至: results/hybrid_run/parsed_data.json

解析結果摘要：
  標題: YouTube 影音資料紀錄
  X 軸: 欄位標題（影片屬性）
  Y 軸: 影片紀錄編號（video_id）
  重要儲存格數: 20

轉換為 AugmenterInput 格式...
  已轉換 20 個儲存格

步驟 2/2: 使用 LLM 生成增強查詢
----------------------------------------------------------------------
生成查詢: 100%|████████████████████| 20/20 [00:15<00:00,  1.3it/s]

✓ 已保存 20 筆增強結果至 results/hybrid_run/augmented_queries.json

======================================================================
處理完成！
======================================================================
總共處理: 20 筆資料

輸出檔案:
  1. Parser 輸出: results/hybrid_run/parsed_data.json
  2. Augmenter 輸出: results/hybrid_run/augmented_queries.json
======================================================================
```

## 常見問題

### Q: Parser 和 Augmenter 可以用不同的模型嗎？

**A:** 可以！這正是使用 YAML 配置的優勢。在配置檔案中分別設定 `parser.llm` 和 `augmenter.llm` 即可。

### Q: 如何在配置檔案中使用環境變數？

**A:** 可以在配置檔案中使用環境變數：

```yaml
augmenter:
  llm:
    api_key: ${OPENROUTER_API_KEY}
```

然後執行：
```bash
export OPENROUTER_API_KEY="your-key"
python scripts/main.py --config config/my_config.yml
```

### Q: 命令列參數和配置檔案有衝突時，哪個優先？

**A:** 命令列參數優先。配置檔案提供預設值，命令列參數可以覆蓋。

### Q: 可以不用配置檔案，純用命令列嗎？

**A:** 可以！只要指定 `--file` 和必要的 LLM 參數即可。

## 配置檔案位置

建議的配置檔案放置位置：

```
augmenter/
├── config/
│   ├── config.example.yml       # 範例配置（本地 vLLM）
│   ├── config.openrouter.yml    # OpenRouter 範例
│   ├── my_config.yml            # 你的自訂配置
│   └── production.yml           # 生產環境配置
└── scripts/
    └── main.py
```

## 進階技巧

### 1. 使用不同的 prompt 測試

```bash
for prompt in 1 2 3; do
  python scripts/main.py \
    --config config/my_config.yml \
    --skip-parser \
    --parsed-output results/base/parsed_data.json \
    --prompt-name $prompt \
    --output-dir results/prompt_$prompt
done
```

### 2. A/B 測試不同模型

```bash
# 測試模型 A
python scripts/main.py \
  --config config/my_config.yml \
  --augmenter-model google/gemini-2.0-flash-exp:free \
  --output-dir results/model_a

# 測試模型 B
python scripts/main.py \
  --config config/my_config.yml \
  --augmenter-model anthropic/claude-3-haiku \
  --output-dir results/model_b
```

## 相關文件

- [Excel Parser LLM 使用說明](../utils/parser/README.md)
- [LLM Augmenter 使用說明](../utils/augmenter/README.md)
- [轉換功能使用說明](../TRANSFORM_USAGE.md)
- [配置檔案範例](../config/)
