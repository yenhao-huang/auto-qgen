# Excel 數據增強服務 API 使用說明

## 簡介

這個 FastAPI 應用程式提供了一個 RESTful API 介面，用於處理 Excel 檔案並生成增強查詢。

## 架構說明

### 主要檔案

1. **[app.py](app.py)** - FastAPI 主應用程式
   - 提供 `/api/v1/data_augment` 端點用於數據增強
   - 處理檔案上傳和 LLM 配置
   - 返回 JSON 格式的結果

2. **[service/augment_service.py](service/augment_service.py)** - 服務類別
   - `AugmentService` 類別封裝了原本 `main.py` 的邏輯
   - 初始化：`service = AugmentService(config, quiet=True)`
   - 執行：`result = service.run(input_file, output_dir)`

3. **[requirements.txt](requirements.txt)** - 依賴套件清單

## 安裝

```bash
# 安裝依賴套件
pip install -r requirements.txt
```

## 啟動服務

```bash
# 啟動 FastAPI 服務（預設端口 8000）
python app.py

# 或使用 uvicorn 直接啟動
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

服務啟動後可以訪問：
- API 文檔（Swagger UI）: http://localhost:8000/docs
- 替代文檔（ReDoc）: http://localhost:8000/redoc

## API 端點

### 1. 數據增強 (data_augment)

**端點**: `POST /api/v1/data_augment`

**功能**: 上傳 Excel 檔案，執行解析和增強查詢生成

**請求參數**:

| 參數名稱 | 類型 | 必填 | 預設值 | 說明 |
|---------|------|------|--------|------|
| file | File | 是 | - | 上傳的 Excel 檔案 (.xlsx) |
| parser_api_key | string | 是 | - | Parser LLM API Key |
| augmenter_api_key | string | 是 | - | Augmenter LLM API Key |
| parser_url | string | 否 | https://openrouter.ai/api | Parser LLM 服務 URL |
| parser_model | string | 否 | z-ai/glm-4.5-air:free | Parser LLM 模型 |
| parser_use_openrouter | boolean | 否 | true | 是否使用 OpenRouter |
| parser_max_retries | integer | 否 | 3 | Parser 最大重試次數 |
| augmenter_url | string | 否 | https://openrouter.ai/api | Augmenter LLM 服務 URL |
| augmenter_model | string | 否 | openai/gpt-oss-20b:free | Augmenter LLM 模型 |
| augmenter_use_openrouter | boolean | 否 | true | 是否使用 OpenRouter |
| augmenter_max_retries | integer | 否 | 3 | Augmenter 最大重試次數 |
| augmenter_prompt_name | string | 否 | default | Augmenter Prompt 名稱 |
| skip_parser | boolean | 否 | false | 是否跳過 Parser 步驟 |

**回應格式**:

```json
{
  "success": true,
  "message": "數據增強完成",
  "parsed_data_path": "results/api_20250115_123456/parsed_data.json",
  "augmented_queries_path": "results/api_20250115_123456/augmented_queries.json",
  "total_count": 10,
  "error": null
}
```

### 2. 下載結果檔案

**端點**: `GET /api/v1/download/{file_type}/{timestamp}`

**功能**: 下載處理結果的 JSON 檔案

**路徑參數**:
- `file_type`: 檔案類型 (`parsed` 或 `augmented`)
- `timestamp`: 處理時的時間戳記（從 data_augment 回應中取得）

### 3. 健康檢查

**端點**: `GET /api/v1/health`

**功能**: 檢查服務狀態

**回應**:
```json
{
  "status": "healthy",
  "service": "Excel 數據增強服務",
  "timestamp": "2025-01-15T12:34:56.789012"
}
```

## 使用範例

### 使用 cURL

```bash
# 數據增強請求
curl -X POST "http://localhost:8000/api/v1/data_augment" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@data.xlsx" \
  -F "parser_api_key=your_parser_api_key" \
  -F "augmenter_api_key=your_augmenter_api_key"

# 下載增強查詢結果
curl -X GET "http://localhost:8000/api/v1/download/augmented/20250115_123456" \
  -o augmented_queries.json
```

### 使用 Python requests

```python
import requests

# 準備檔案和參數
files = {
    'file': open('data.xlsx', 'rb')
}

data = {
    'parser_api_key': 'your_parser_api_key',
    'augmenter_api_key': 'your_augmenter_api_key',
    'parser_model': 'z-ai/glm-4.5-air:free',
    'augmenter_model': 'openai/gpt-oss-20b:free'
}

# 發送請求
response = requests.post(
    'http://localhost:8000/api/v1/data_augment',
    files=files,
    data=data
)

# 處理回應
result = response.json()
print(f"Success: {result['success']}")
print(f"Total Count: {result['total_count']}")
print(f"Output Path: {result['augmented_queries_path']}")
```

### 使用 Swagger UI (瀏覽器)

1. 開啟瀏覽器訪問 http://localhost:8000/docs
2. 找到 `/api/v1/data_augment` 端點
3. 點擊 "Try it out"
4. 上傳 Excel 檔案並填寫必要參數
5. 點擊 "Execute" 執行請求
6. 查看回應結果

## 服務類別使用範例（程式碼中直接使用）

```python
from pathlib import Path
from service.augment_service import AugmentService

# 配置
config = {
    "parser": {
        "llm": {
            "url": "https://openrouter.ai/api",
            "model": "z-ai/glm-4.5-air:free",
            "api_key": "your_api_key",
            "use_openrouter": True,
            "max_retries": 3
        }
    },
    "augmenter": {
        "llm": {
            "url": "https://openrouter.ai/api",
            "model": "openai/gpt-oss-20b:free",
            "api_key": "your_api_key",
            "use_openrouter": True,
            "max_retries": 3
        },
        "prompt_name": "default"
    }
}

# 初始化服務
service = AugmentService(config=config, quiet=False)

# 執行數據增強
result = service.run(
    input_file=Path("data.xlsx"),
    output_dir=Path("results/output")
)

# 檢查結果
if result["success"]:
    print(f"處理成功！共 {result['total_count']} 筆資料")
    print(f"輸出路徑: {result['augmented_queries_path']}")
else:
    print(f"處理失敗: {result['error']}")
```

## 目錄結構

```
augmenter/
├── app.py                          # FastAPI 主應用程式
├── service/
│   ├── __init__.py                 # Package 初始化
│   └── augment_service.py          # 服務類別
├── requirements.txt                # 依賴套件
├── config/                         # 配置檔案目錄
├── results/                        # 結果輸出目錄
│   └── api_{timestamp}/           # 每次 API 請求的輸出
│       ├── parsed_data.json
│       └── augmented_queries.json
└── temp/                           # 臨時檔案目錄
```

## 注意事項

1. **API Key 安全性**: 請勿在程式碼中硬編碼 API Key，建議使用環境變數或配置檔案
2. **檔案大小限制**: 預設無檔案大小限制，可在 FastAPI 中配置 `max_upload_size`
3. **結果檔案清理**: `results/` 和 `temp/` 目錄中的檔案需要定期清理
4. **並發處理**: 目前服務為同步處理，如需高並發可考慮使用 Celery 等任務佇列

## 錯誤處理

API 會返回以下 HTTP 狀態碼：

- `200`: 請求成功
- `400`: 請求參數錯誤（如檔案格式不正確）
- `404`: 找不到資源（如下載不存在的檔案）
- `500`: 伺服器內部錯誤（如 LLM 處理失敗）

錯誤回應格式：
```json
{
  "detail": "錯誤訊息描述"
}
```

## 維護和擴展

如需新增功能或修改邏輯：

1. **修改服務邏輯**: 編輯 [service/augment_service.py](service/augment_service.py)
2. **新增 API 端點**: 在 [app.py](app.py) 中新增路由
3. **調整配置**: 修改預設參數或新增配置選項

## 授權

請參考專案根目錄的 LICENSE 檔案。
