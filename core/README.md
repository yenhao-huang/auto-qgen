# Excel Augment Service

將 Excel 解析與增強查詢封裝為簡單的 function 形式，提供完整的資料處理流程。

## 功能

執行完整的 4 步驟流程：

1. **Parser**: 使用 LLM 解析 Excel 檔案
2. **Transform**: 將解析結果轉換為 AugmenterInput 格式
3. **Augment**: 使用 LLM 生成增強查詢
4. **Output**: 儲存結果到 JSON 檔案

## 使用方式

### 方式 1: 命令列使用

```bash
# 使用預設配置檔 (configs/excel_augment.example.yml)
python core/excel_augment.py

# 使用自訂配置檔
python core/excel_augment.py --config configs/my_config.yml
```

### 方式 2: 作為模組使用

```python
from pathlib import Path
from core.excel_augment import load_config, run

# 從配置檔載入
config = load_config(Path("configs/excel_augment.example.yml"))
result = run(config=config)

# 檢查結果
if result["success"]:
    print(f"成功處理 {result['total_count']} 筆資料")
    print(f"Parser 輸出: {result['parsed_data_path']}")
    print(f"Augmenter 輸出: {result['augmented_queries_path']}")
```

### 方式 3: 直接使用字典配置

```python
from core.excel_augment import run

config = {
    "input": {
        "file_path": "data/example.xlsx",
        "skip_parser": False
    },
    "output": {
        "dir": "results/my_output"
    },
    "verbose": True,
    "parser": {
        "llm": {
            "url": "http://localhost:8000/v1",
            "model": "my-model",
            "api_key": None,
            "use_openrouter": False,
            "max_retries": 3
        }
    },
    "augmenter": {
        "prompt_name": "default",
        "llm": {
            "url": "http://localhost:8000/v1",
            "model": "my-model",
            "api_key": None,
            "use_openrouter": False,
            "max_tokens": 18000,
            "temperature": 0.7
        }
    }
}

result = run(config=config)
```

## 配置檔格式

請參考 `configs/excel_augment.example.yml` 範例配置檔：

```yaml
# 輸入設定
input:
  file_path: "data/example.xlsx"      # 必填：輸入 Excel 檔案路徑
  skip_parser: false                  # 是否跳過 Parser 步驟
  # parsed_data_path: "..."           # skip_parser=true 時使用

# 輸出設定
output:
  dir: "results/my_output"            # 輸出目錄（留空則使用 timestamp）

# 顯示設定
verbose: true                         # 是否顯示詳細訊息和進度條

# Parser LLM 設定
parser:
  llm:
    url: "http://localhost:8000/v1"
    model: "your-model"
    api_key: null
    use_openrouter: false
    max_retries: 3

# Augmenter LLM 設定
augmenter:
  prompt_name: "default"
  llm:
    url: "http://localhost:8000/v1"
    model: "your-model"
    api_key: null
    use_openrouter: false
    max_tokens: 18000
    temperature: 0.7
```

## 進階用法

### 跳過 Parser 步驟

如果已經有解析好的資料，可以跳過 Parser 直接執行 Augment：

```yaml
input:
  file_path: "data/dummy.xlsx"        # 不會被使用
  skip_parser: true
  parsed_data_path: "results/excel/parsed_data.json"
```

### 使用 OpenRouter

```yaml
augmenter:
  llm:
    url: "https://openrouter.ai/api/v1"
    model: "anthropic/claude-3.5-sonnet"
    api_key: "your-openrouter-api-key"
    use_openrouter: true
```

## 輸出結果

執行成功後會返回：

```python
{
    "success": True,
    "parsed_data_path": "results/.../parsed_data.json",
    "augmented_queries_path": "results/.../augmented_queries.json",
    "augmented_queries": [...],
    "total_count": 10
}
```

## 範例程式碼

完整的使用範例請參考 `plans/usage_example.py`

## API 參考

### `load_config(config_path: Path) -> Dict[str, Any]`

載入 YAML 配置檔案

### `run(config: Dict[str, Any]) -> Dict[str, Any]`

執行完整的資料增強流程，所有參數從 config 讀取
