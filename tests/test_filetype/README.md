# 文件類型測試套件

這個測試套件用於測試 auto-gen-multimodel 專案中不同文件類型（Excel、Image、PDF）的處理流程。

## 測試文件結構

```
tests/test_filetype/
├── __init__.py                 # 套件初始化文件
├── test_excel.py               # Excel 文件類型測試
├── test_image.py               # Image 文件類型測試
├── test_pdf.py                 # PDF 文件類型測試
├── run_all_tests.py            # 統一測試執行器
└── README.md                   # 本文件

tests/testcases/filetypes/
├── 表7-3-2.xlsx                # Excel 測試文件
├── (檔案下載)113年度長期照顧服務機構評鑑結果-第一批次名單_page_0002.png  # Image 測試文件
└── (公告)109年度獎助布建住宿式長照機構公共化資源計畫.pdf  # PDF 測試文件
```

## 測試範圍

### 1. Excel 測試 (`test_excel.py`)

測試 Excel Pipeline 的功能，包括：

- **文件類型檢測**
  - 測試 `.xlsx`, `.xls`, `.xlsm`, `.xlsb` 等格式的識別
  - 測試自動檢測和顯式指定 Pipeline 類型

- **配置文件處理**
  - 測試配置文件的載入和解析
  - 測試配置結構的正確性
  - 測試範例配置文件的兼容性

- **Pipeline 執行**（需要 LLM 服務）
  - 測試完整的 Parser + Augmenter 流程
  - 測試配置驗證

### 2. Image 測試 (`test_image.py`)

測試 Image Pipeline 的功能，包括：

- **文件類型檢測**
  - 測試 `.png`, `.jpg`, `.jpeg`, `.bmp`, `.gif`, `.tiff`, `.webp` 等格式的識別
  - 測試自動檢測和顯式指定 Pipeline 類型

- **OCR 引擎測試**
  - 測試支援的 OCR 引擎（paddle, dots, chandra, nv_nemotron）
  - 測試不同的 OCR 模式（local, vllm, openrouter）

- **配置文件處理**
  - 測試 OCR 配置的載入和解析
  - 測試問題生成配置的載入和解析
  - 測試 OCR-only 模式

- **Pipeline 執行**（需要 OCR 服務）
  - 測試完整的 OCR + 問題生成流程
  - 測試只執行 OCR 的流程
  - 測試目錄輸入處理

### 3. PDF 測試 (`test_pdf.py`)

測試 PDF Pipeline 的功能，包括：

- **文件類型檢測**
  - 測試 `.pdf` 格式的識別
  - 測試自動檢測和顯式指定 Pipeline 類型

- **PDF 轉換測試**
  - 測試 PDF 轉圖片的參數設定（DPI, 格式, 最大尺寸）
  - 測試轉換器的初始化
  - 測試支援的輸出格式（PNG, JPEG）

- **配置文件處理**
  - 測試轉換配置的載入和解析
  - 測試 OCR 配置的載入和解析
  - 測試問題生成配置的載入和解析

- **Pipeline 執行**（需要 PDF 處理服務）
  - 測試完整的 PDF 轉換 + OCR + 問題生成流程
  - 測試只執行 OCR 的流程

## 使用方法

### 基本用法

#### 1. 執行所有測試

```bash
# 基本模式
python tests/test_filetype/run_all_tests.py

# 詳細輸出模式
python tests/test_filetype/run_all_tests.py -v
```

#### 2. 執行特定文件類型的測試

```bash
# 只測試 Excel
python tests/test_filetype/run_all_tests.py --excel

# 只測試 Image
python tests/test_filetype/run_all_tests.py --image

# 只測試 PDF
python tests/test_filetype/run_all_tests.py --pdf
```

#### 3. 執行基本測試（不需要服務）

```bash
# 只執行不需要實際服務的測試
python tests/test_filetype/run_all_tests.py --basic
```

### 使用 pytest 直接執行

#### 1. 執行所有測試

```bash
cd /tmp2/howard/auto-gen-multimodel
pytest tests/test_filetype/ -v
```

#### 2. 執行單個測試文件

```bash
# 測試 Excel
pytest tests/test_filetype/test_excel.py -v

# 測試 Image
pytest tests/test_filetype/test_image.py -v

# 測試 PDF
pytest tests/test_filetype/test_pdf.py -v
```

#### 3. 執行特定測試類別

```bash
# 執行 Excel 文件類型測試類別
pytest tests/test_filetype/test_excel.py::TestExcelFileType -v

# 執行 Image Pipeline 集成測試類別
pytest tests/test_filetype/test_image.py::TestImagePipelineIntegration -v
```

#### 4. 執行特定測試函數

```bash
# 執行特定測試
pytest tests/test_filetype/test_excel.py::TestExcelFileType::test_file_exists -v
```

#### 5. 跳過需要服務的測試

```bash
# 只執行不需要實際服務的測試
pytest tests/test_filetype/ -v -m "not skip"
```

### 進階用法

#### 1. 顯示測試覆蓋率

```bash
pytest tests/test_filetype/ --cov=core --cov-report=html
```

#### 2. 平行執行測試（需要 pytest-xdist）

```bash
pytest tests/test_filetype/ -v -n auto
```

#### 3. 只執行失敗的測試

```bash
pytest tests/test_filetype/ --lf
```

## 測試標記（Markers）

測試使用以下 pytest markers：

- `@pytest.mark.skip`: 標記需要實際服務運行的測試
- `@pytest.mark.skipif`: 條件性跳過測試（例如：缺少配置文件）

## 依賴套件

執行測試需要以下套件：

```bash
pip install pytest pytest-cov pyyaml
```

可選套件（提升測試體驗）：

```bash
pip install pytest-xdist  # 平行執行測試
```

## 測試數據

測試使用 `tests/testcases/filetypes/` 目錄下的真實文件：

1. **Excel 文件**: `表7-3-2.xlsx`
   - 用於測試 Excel Parser 和 Augmenter

2. **Image 文件**: `(檔案下載)113年度長期照顧服務機構評鑑結果-第一批次名單_page_0002.png`
   - 用於測試 OCR 和問題生成

3. **PDF 文件**: `(公告)109年度獎助布建住宿式長照機構公共化資源計畫.pdf`
   - 用於測試 PDF 轉換、OCR 和問題生成

## 注意事項

1. **跳過的測試**: 某些測試標記為 `@pytest.mark.skip`，因為它們需要實際的服務運行（如 LLM 服務、OCR 服務）

2. **測試隔離**: 每個測試使用臨時目錄（`tmp_path` fixture）確保測試之間的隔離

3. **配置文件**: 測試會動態生成測試用的配置文件，不會影響專案的實際配置

4. **錯誤處理**: 測試涵蓋了正常情況和錯誤情況（如文件不存在、配置錯誤等）

## 擴展測試

如需添加新的測試：

1. 在對應的測試文件中添加新的測試類別或測試函數
2. 使用 pytest fixtures 來共享測試數據和設置
3. 使用適當的 markers 標記需要特殊處理的測試
4. 更新本 README 文件說明新增的測試範圍

## 問題排查

### 測試失敗

1. 檢查測試文件是否存在於 `tests/testcases/filetypes/`
2. 確認專案根目錄路徑設置正確
3. 檢查 Python 路徑是否包含專案根目錄

### Import 錯誤

確保從專案根目錄執行測試，或正確設置 `PYTHONPATH`：

```bash
export PYTHONPATH=/tmp2/howard/auto-gen-multimodel:$PYTHONPATH
pytest tests/test_filetype/ -v
```

## 貢獻

歡迎提交 Pull Request 來改進測試套件！請確保：

1. 新增的測試有清晰的文檔說明
2. 測試名稱具有描述性
3. 適當使用 fixtures 來減少重複代碼
4. 更新 README 文件說明新增的測試

## 授權

本測試套件遵循專案的授權協議。
