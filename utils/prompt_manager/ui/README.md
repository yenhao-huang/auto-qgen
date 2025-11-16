# Prompt Manager UI

視覺化介面來管理 LLM Prompts

## 功能

1. **📋 查看 Prompts** - 瀏覽所有已存在的 prompts
2. **➕ 新增 Prompt** - 透過表單新增新的 prompt
3. **✏️ 編輯 Prompt** - 修改現有的 prompt
4. **🗑️ 刪除 Prompt** - 刪除不需要的 prompt
5. **🧪 測試 Prompt** - 測試生成的 prompt 文字

## 安裝依賴

```bash
pip install streamlit
```

## 啟動應用

```bash
cd /tmp2/howard/TIRS/ext/eval_metadata/llm_for_evaluator/prompt_manager/ui
streamlit run app.py
```

或使用提供的啟動腳本：

```bash
./run.sh
```

## 使用說明

### 1. 查看 Prompts

- 選擇左側選單的「📋 查看 Prompts」
- 從下拉選單選擇要查看的 prompt
- 查看 prompt 的所有設定

### 2. 新增 Prompt

- 選擇「➕ 新增 Prompt」
- **選擇基礎模板**：
  - ✅ 勾選「以 Default Prompt 為基礎」（預設勾選）
  - 表單會自動填入 default prompt 的內容
  - 您可以在此基礎上修改，快速建立新 prompt
  - 取消勾選則從空白開始
- 填寫表單：
  - **Prompt 名稱**：唯一識別符（建議使用英文和底線）
  - **系統角色**：定義 LLM 的角色（已預填）
  - **任務描述**：說明要完成的任務（已預填）
  - **要求列表**：列出具體要求（已預填）
  - **輸出格式**：指定輸出格式（已預填）
  - **示範範例**（可選）：提供範例
- 點擊「新增 Prompt」按鈕

### 3. 編輯 Prompt

- 選擇「✏️ 編輯 Prompt」
- 選擇要編輯的 prompt
- 修改欄位內容
- 點擊「更新 Prompt」按鈕

### 4. 刪除 Prompt

- 選擇「🗑️ 刪除 Prompt」
- 選擇要刪除的 prompt（default prompt 無法刪除）
- 確認刪除操作

### 5. 測試 Prompt

- 選擇「🧪 測試 Prompt」
- 選擇要測試的 prompt
- 輸入測試資料
- 點擊「生成 Prompt」查看結果

## 配置文件

所有 prompts 自動儲存到：
```
/tmp2/howard/TIRS/ext/eval_metadata/llm_for_evaluator/prompt_manager/prompts_config.yml
```

## 注意事項

1. **Prompt 名稱**必須唯一
2. **default prompt** 無法刪除
3. 所有修改會自動儲存到 YAML 文件
4. 建議定期備份 `prompts_config.yml`

## 螢幕截圖

### 查看 Prompts
![查看介面](./screenshots/view.png)

### 新增 Prompt
![新增介面](./screenshots/add.png)

### 測試 Prompt
![測試介面](./screenshots/test.png)

## 疑難排解

### 問題：應用無法啟動

**解決**：
- 確認已安裝 streamlit：`pip install streamlit`
- 確認 Python 版本 >= 3.7

### 問題：找不到配置文件

**解決**：
- 應用會自動創建預設配置
- 確認有寫入權限到目標目錄

### 問題：Prompt 沒有儲存

**解決**：
- 檢查表單是否所有必填欄位都已填寫
- 檢查終端輸出的錯誤訊息
- 確認 YAML 文件的寫入權限
