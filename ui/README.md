# Web UI 使用說明

## 功能特色

- **左側欄位**
  - 檔案上傳區
  - 處理狀態顯示
  - **圖片/PDF 預覽**（新功能）
    - 圖片檔案：顯示原始圖片
    - PDF 檔案：顯示所有轉換後的頁面圖片（Gallery 模式）

- **右側欄位**
  - 生成的問題列表

## 快速啟動

### 方法 1: 使用啟動腳本（推薦）

```bash
cd ui
./run.sh
```

### 方法 2: 直接執行

```bash
# 安裝依賴
pip install gradio pillow

# 啟動 Web UI
cd ui
python web_ui.py
```

## 訪問 UI

啟動後，在瀏覽器中打開：

```
http://localhost:7860
```

## 使用方法

1. **上傳檔案**
   - 點擊「選擇檔案」按鈕
   - 選擇您要處理的檔案（Excel、圖片或 PDF）

2. **預覽檔案**（圖片/PDF）
   - 上傳圖片後，會在左下方顯示圖片預覽
   - 上傳 PDF 後，會在左下方顯示所有頁面的圖片預覽（Gallery）

3. **開始處理**
   - 點擊「開始處理」按鈕
   - 等待處理完成

4. **查看結果**
   - 左上方顯示處理狀態
   - 右側顯示生成的問題列表

## 支援的檔案格式

### Excel
- `.xlsx` - Excel 2007+ 格式
- `.xls` - Excel 97-2003 格式
- `.xlsm` - Excel 啟用巨集的活頁簿
- `.xlsb` - Excel 二進位活頁簿

### 圖片
- `.png` - PNG 圖片
- `.jpg` / `.jpeg` - JPEG 圖片
- `.bmp` - 點陣圖
- `.gif` - GIF 圖片
- `.tiff` - TIFF 圖片
- `.webp` - WebP 圖片

### PDF
- `.pdf` - PDF 文件

## 配置

Web UI 會自動載入 `configs/unified_pipeline.example.yml` 作為預設配置。

如果該檔案不存在，將使用內建的預設配置。

### 自訂配置

如需自訂配置，請編輯 `configs/unified_pipeline.example.yml` 文件。

主要配置項目：
- `excel`: Excel 處理配置
- `image`: 圖片處理配置（OCR、生成問題）
- `pdf`: PDF 處理配置（轉換、OCR、生成問題）
- `metadata`: 元數據

## 輸出

處理結果會保存在 `results/web_ui/` 目錄下：

- Excel 處理結果: `results/web_ui/excel/`
- 圖片 OCR 結果: `results/web_ui/ocr/`
- PDF 處理結果: `results/web_ui/pdf_ocr/`
- PDF 轉換圖片: `results/web_ui/pdf_images/`

生成的問題會保存為 `augmented_queries.json`

## UI 預覽說明

### 圖片檔案
上傳圖片後，左側會顯示：
- 處理狀態（上方）
- 圖片預覽（下方）

### PDF 檔案
上傳 PDF 後，左側會顯示：
- 處理狀態（上方）
- 所有頁面的圖片預覽 Gallery（下方）
  - 每頁顯示為獨立圖片
  - 可以點擊放大查看

### Excel 檔案
上傳 Excel 後，左側會顯示：
- 處理狀態（上方）
- 無預覽（Excel 不支援預覽）

## 注意事項

1. **確保後端服務正在運行**
   - VLLM 服務（如果使用 vllm 模式）
   - OpenRouter API key（如果使用 openrouter 模式）

2. **處理時間**
   - Excel 檔案：通常較快
   - 圖片檔案：取決於 OCR 服務
   - PDF 檔案：需要先轉換為圖片，耗時較長

3. **記憶體使用**
   - 大型 PDF 檔案可能需要較多記憶體
   - 建議處理前確保有足夠的可用記憶體

4. **依賴套件**
   - `gradio`: Web UI 框架
   - `pillow`: 圖片處理（用於預覽）

## 疑難排解

### 無法啟動 Web UI

檢查是否已安裝所需套件：
```bash
pip install gradio pillow
```

### 處理失敗

1. 檢查配置文件是否正確
2. 確認後端服務（VLLM）是否正在運行
3. 查看錯誤訊息了解具體問題

### 圖片無法顯示

確認已安裝 pillow：
```bash
pip install pillow
```

### 埠號已被占用

如需更改埠號，編輯 `web_ui.py` 中的 `server_port` 參數：
```python
demo.launch(
    server_name="0.0.0.0",
    server_port=7860,  # 修改此處
    share=False
)
```

## 進階功能

### 分享 UI（公開訪問）

如需透過網際網路分享 UI，修改 `web_ui.py`：
```python
demo.launch(
    server_name="0.0.0.0",
    server_port=7860,
    share=True  # 設定為 True
)
```

這會生成一個臨時的公開 URL，可以分享給其他人使用。

### 自訂主題

Web UI 使用 `gr.themes.Soft()` 主題，您可以在 `create_ui()` 函數中修改：

```python
with gr.Blocks(title="Auto-Gen MultiModel", theme=gr.themes.Default()) as demo:
```

可用主題：
- `gr.themes.Soft()` - 柔和主題（預設）
- `gr.themes.Default()` - 預設主題
- `gr.themes.Monochrome()` - 單色主題
- `gr.themes.Glass()` - 玻璃主題
