# 測試說明

## 測試檔案

### 1. test_excel_pipeline.py
Excel Pipeline 完整測試，包含 Parser、Transform、Augmenter 的功能測試。

**使用方法：**
```bash
# 使用 pytest 執行
pytest tests/test_excel_pipeline.py -v

# 直接執行（無需 pytest）
python tests/test_excel_pipeline.py
```

**測試內容：**
- Excel Parser 初始化與載入
- 單檔和批次模式
- 欄位名稱轉換
- 轉換為 AugmenterInput
- 錯誤處理
- 完整 Pipeline 整合

---

### 2. test_main_batch.py
測試 main.py 對批次處理的支援。

**使用方法：**
```bash
# 使用 pytest 執行
pytest tests/test_main_batch.py -v

# 直接執行
python tests/test_main_batch.py
```

**測試內容：**
- 檔案類型偵測（檔案/目錄）
- Pipeline 類型自動判斷
- 單檔與批次模式配置構建
- 批次模式配置結構驗證

---

### 3. test_input_dir.py
執行實際的 Pipeline 測試，依次運行多種格式的配置檔案。

**使用方法：**
```bash
# 直接執行（會運行所有 test_*.yml 配置）
python tests/test_input_dir.py
```

**測試配置：**
- `test_excel.yml` - Excel 檔案處理
- `test_pdf.yml` - PDF 檔案處理
- `test_png.yml` - PNG 圖片處理
- `test_mix.yml` - 混合格式處理

**說明：**
此測試會實際執行 Pipeline 並產生結果檔案。

---

## 快速開始

```bash
# 執行所有測試
python tests/test_excel_pipeline.py
python tests/test_main_batch.py
python tests/test_input_dir.py

# 或使用 pytest
pytest tests/ -v
```
