# 測試套件安裝指南

## 前置需求

### Python 版本
- Python 3.8 或更高版本

### 安裝測試依賴

#### 1. 安裝核心測試套件

```bash
pip install pytest>=6.0.0 pytest-cov>=2.12.0 pyyaml>=5.4.0
```

#### 2. 安裝可選依賴（建議）

```bash
pip install pytest-xdist>=2.3.0  # 平行執行測試
pip install pytest-html>=3.1.0   # 生成 HTML 測試報告
```

#### 3. 使用 requirements.txt 一次安裝

```bash
cd tests/test_filetype
pip install -r requirements.txt
```

## 驗證安裝

### 檢查 pytest 是否安裝成功

```bash
pytest --version
```

應該顯示類似：
```
pytest 7.x.x
```

### 檢查測試文件是否存在

```bash
ls -la tests/testcases/filetypes/
```

應該顯示三個測試文件：
- `表7-3-2.xlsx` (Excel)
- `(檔案下載)113年度長期照顧服務機構評鑑結果-第一批次名單_page_0002.png` (Image)
- `(公告)109年度獎助布建住宿式長照機構公共化資源計畫.pdf` (PDF)

## 執行測試

### 快速開始

```bash
# 從專案根目錄執行
cd /tmp2/howard/auto-gen-multimodel

# 執行所有測試（基本測試，不需要服務）
pytest tests/test_filetype/ -v -m "not skip"

# 或使用測試執行器
python tests/test_filetype/run_all_tests.py --basic -v
```

### 使用簡單測試執行器（不需要 pytest）

如果環境中沒有安裝 pytest，可以使用簡單測試執行器：

```bash
python tests/test_filetype/simple_runner.py
```

這個執行器不需要任何額外的測試框架，只會執行基本的文件類型檢測測試。

## 故障排除

### 問題 1: ModuleNotFoundError: No module named 'pytest'

**解決方法：**
```bash
pip install pytest
```

### 問題 2: ModuleNotFoundError: No module named 'yaml'

**解決方法：**
```bash
pip install pyyaml
```

### 問題 3: 找不到測試文件

**解決方法：**
確保從專案根目錄執行測試，或設置 PYTHONPATH：
```bash
export PYTHONPATH=/tmp2/howard/auto-gen-multimodel:$PYTHONPATH
pytest tests/test_filetype/ -v
```

### 問題 4: 測試需要實際服務但服務未運行

某些測試標記為 `@pytest.mark.skip`，因為它們需要實際的服務（如 LLM 服務、OCR 服務）。

**解決方法：**
只執行不需要服務的測試：
```bash
pytest tests/test_filetype/ -v -m "not skip"
```

## 測試環境設置

### 1. 完整環境（包含服務）

如果您想執行完整的集成測試（包含需要服務的測試），需要：

1. **LLM 服務**（用於 Excel 和問題生成）
   - 設置 vllm 或 OpenRouter 服務
   - 更新配置文件中的 URL 和模型名稱

2. **OCR 服務**（用於圖片和 PDF）
   - 設置 PaddleOCR 或其他 OCR 引擎
   - 更新配置文件中的 URL 和引擎設置

### 2. 基本環境（只測試配置和文件類型檢測）

不需要任何服務，只需要：
- Python 3.8+
- pytest（或使用 simple_runner.py）
- 測試文件存在於 `tests/testcases/filetypes/`

## 建議的測試流程

### 開發階段

```bash
# 1. 快速檢查基本功能
python tests/test_filetype/simple_runner.py

# 2. 執行單元測試
pytest tests/test_filetype/ -v -m "not skip"

# 3. 執行特定文件類型測試
pytest tests/test_filetype/test_excel.py -v -m "not skip"
```

### CI/CD 集成

```bash
# 執行所有不需要外部服務的測試
pytest tests/test_filetype/ -v -m "not skip" --cov=core --cov-report=xml
```

### 完整測試（需要服務）

```bash
# 執行所有測試（包含集成測試）
pytest tests/test_filetype/ -v
```

## 下一步

閱讀 [README.md](README.md) 了解更多測試使用方法和詳細說明。
