# Prompt Manager - 簡化版

簡單直觀的 Prompt 管理系統，支援透過 `prompt_name` 來管理和使用 prompts。

## 概述

這個簡化版的 Prompt Manager 提供：

1. ✅ **簡單的 API** - 透過 `prompt_name` 新增、取得、更新、刪除 prompts
2. ✅ **自動載入** - 從 YAML 文件自動載入已存在的 prompts
3. ✅ **預設回退** - 找不到 prompt 時自動使用預設 prompt
4. ✅ **Streamlit UI** - 視覺化介面管理 prompts
5. ✅ **與 Augmenter 整合** - 無縫整合到現有的 LLMAugmenter

## 快速開始

### 基本使用

```python
from prompt_manager import PromptManager

# 初始化
pm = PromptManager()

# 列出所有 prompts
print(pm.list_prompts())

# 使用預設 prompt 生成文字
prompt_text = pm.generate_prompt_text(
    prompt_name="default",
    context="您的輸入資料"
)
```

### 新增自訂 Prompt

```python
pm.add_prompt(
    prompt_name="my_medical_expert",
    system_role="你是一位資深的醫療統計專家。",
    task="請生成5個專業的查詢句子。",
    requirements=[
        "使用專業術語",
        "關注數據準確性",
        "包含時間序列比較"
    ],
    output_formats=[
        "1. [查詢句子 1]",
        "2. [查詢句子 2]",
        "3. [查詢句子 3]",
        "4. [查詢句子 4]",
        "5. [查詢句子 5]"
    ],
    demonstrations=[  # 可選
        "範例：112年的服務人次與111年相比增加了多少？"
    ]
)
```

### 與 LLMAugmenter 整合

```python
from llm_augmenter import LLMAugmenterByKeyword
from prompt_manager import PromptManager

# 創建 PromptManager
pm = PromptManager()

# 新增自訂 prompt（或使用已存在的）
pm.add_prompt(...)

# 在 Augmenter 中使用
augmenter = LLMAugmenterByKeyword(
    vllm_url="http://192.168.1.79:3472",
    model="gemma-12b-8bit",
    prompt_name="my_medical_expert",  # 指定 prompt 名稱
    prompt_manager=pm  # 傳入 PromptManager
)

# 執行增強
result = augmenter.augment(keyword_input)
```

## PromptConfig 結構

每個 prompt 包含以下欄位：

```python
@dataclass
class PromptConfig:
    prompt_name: str              # Prompt 名稱（唯一識別符）
    system_role: str              # 系統角色
    task: str                     # 任務描述
    requirements: List[str]       # 要求列表
    output_formats: List[str]     # 輸出格式範例
    demonstrations: Optional[List[str]]  # 示範範例（可選）
```

### 範例

```python
{
    "prompt_name": "medical_expert",
    "system_role": "你是一位醫療資料分析專家。",
    "task": "請根據以下正式的醫療統計資料，生成3-5個不同的口語化查詢句子。",
    "requirements": [
        "生成的查詢句子要自然、口語化",
        "包含不同的問法和角度",
        "保持專業性但避免過於正式",
        "每個句子都要能夠找到這筆資料",
        "句子長度適中"
    ],
    "output_formats": [
        "1. [第一個查詢句子]",
        "2. [第二個查詢句子]",
        "3. [第三個查詢句子]",
        "4. [第四個查詢句子]",
        "5. [第五個查詢句子]"
    ],
    "demonstrations": None
}
```

## API 參考

### PromptManager

#### 初始化

```python
pm = PromptManager(config_file: Optional[str] = None)
```

- `config_file`: YAML 配置文件路徑（可選，預設使用 `prompts_config.yml`）

#### 主要方法

**新增 Prompt:**

```python
pm.add_prompt(
    prompt_name: str,
    system_role: str,
    task: str,
    requirements: List[str],
    output_formats: List[str],
    demonstrations: Optional[List[str]] = None,
    save_to_file: bool = True
)
```

**取得 Prompt:**

```python
config = pm.get_prompt(
    prompt_name: str,
    use_default_if_not_found: bool = True
)
```

**生成 Prompt 文字:**

```python
text = pm.generate_prompt_text(
    prompt_name: str,
    context: str,
    use_default_if_not_found: bool = True
)
```

**更新 Prompt:**

```python
pm.update_prompt(
    prompt_name: str,
    system_role: Optional[str] = None,
    task: Optional[str] = None,
    requirements: Optional[List[str]] = None,
    output_formats: Optional[List[str]] = None,
    demonstrations: Optional[List[str]] = None,
    save_to_file: bool = True
)
```

**刪除 Prompt:**

```python
pm.delete_prompt(
    prompt_name: str,
    save_to_file: bool = True
)
```

**列出所有 Prompts:**

```python
prompts = pm.list_prompts()
```

## Streamlit UI

### 啟動方式

```bash
cd prompt_manager/ui
streamlit run app.py
```

或使用提供的腳本：

```bash
./prompt_manager/ui/run.sh
```

### 功能

1. **📋 查看 Prompts** - 瀏覽所有已存在的 prompts
2. **➕ 新增 Prompt** - 透過表單新增新的 prompt
   - ✨ **預設以 default prompt 為基礎** - 表單會自動填入 default prompt 的內容
   - 您可以在此基礎上修改，快速建立新 prompt
   - 可選擇取消勾選「以 Default Prompt 為基礎」從空白開始
3. **✏️ 編輯 Prompt** - 修改現有的 prompt
4. **🗑️ 刪除 Prompt** - 刪除不需要的 prompt
5. **🧪 測試 Prompt** - 測試生成的 prompt 文字

詳細說明請參考 [ui/README.md](ui/README.md)

## 文件結構

```
prompt_manager/
├── __init__.py              # Package 初始化
├── manager.py               # PromptManager 核心類別
├── prompts_config.yml       # Prompt 配置文件
├── example.py               # 使用範例
├── README.md                # 本文件
└── ui/                      # Streamlit UI
    ├── app.py              # UI 應用程式
    ├── run.sh              # 啟動腳本
    └── README.md           # UI 文檔
```

## 使用場景

### 場景 1: 快速原型開發

```python
pm = PromptManager()

# 使用預設 prompt 快速開始
augmenter = LLMAugmenterByKeyword(
    vllm_url="...",
    model="...",
    prompt_name="default"  # 使用預設
)
```

### 場景 2: A/B 測試不同 Prompts

```python
pm = PromptManager()

# 測試版本 A
pm.add_prompt(prompt_name="version_a", ...)
augmenter_a = LLMAugmenterByKeyword(..., prompt_name="version_a")

# 測試版本 B
pm.add_prompt(prompt_name="version_b", ...)
augmenter_b = LLMAugmenterByKeyword(..., prompt_name="version_b")

# 比較結果
results_a = evaluate(augmenter_a)
results_b = evaluate(augmenter_b)
```

### 場景 3: 使用 UI 管理 Prompts

```bash
# 啟動 UI
cd prompt_manager/ui
streamlit run app.py

# 在 UI 中新增/編輯 prompts

# 在程式碼中使用
pm = PromptManager()  # 自動載入 UI 中新增的 prompts
augmenter = LLMAugmenterByKeyword(..., prompt_name="ui_created_prompt")
```

## 預設 Prompts

系統內建以下 prompts（來自舊配置文件）：

1. **default** - 預設版本
2. **senior_expert** - 資深專家版本
3. **concise** - 簡潔版本
4. **detailed** - 詳細版本
5. **experimental** - 實驗版本

## 測試

執行測試：

```bash
# 測試 PromptManager
.venv/bin/python prompt_manager/manager.py

# 執行使用範例
.venv/bin/python prompt_manager/example.py
```

## 最佳實踐

### 1. Prompt 命名

使用描述性的名稱：
- ✅ `medical_expert_detailed`
- ✅ `policy_analysis_formal`
- ❌ `prompt1`
- ❌ `test`

### 2. 定期備份

```bash
cp prompts_config.yml prompts_config_backup_$(date +%Y%m%d).yml
```

### 3. 共享 PromptManager

在同一應用中共享 PromptManager 實例：

```python
# 創建一次
pm = PromptManager()

# 多個 augmenter 共享
augmenter1 = LLMAugmenterByKeyword(..., prompt_manager=pm)
augmenter2 = LLMAugmenterByKeyword(..., prompt_manager=pm)
```

### 4. 測試新 Prompt

在套用到正式環境前，先使用 UI 的測試功能驗證：

1. 在 UI 中新增 prompt
2. 使用「🧪 測試 Prompt」功能
3. 確認生成的結果符合預期
4. 在程式碼中使用

## 與舊版本的差異

### 舊版本（v1.0/v2.0）

```python
pm = PromptManager(
    config_file="prompts_config.yml",
    version="concise"  # 選擇版本
)
```

### 新版本（v3.0 - 簡化版）

```python
pm = PromptManager()  # 自動載入所有 prompts

# 直接透過 prompt_name 使用
pm.generate_prompt_text(
    prompt_name="concise",  # 直接指定名稱
    context="..."
)
```

**主要改進**：

1. ✅ 更簡單的 API
2. ✅ 不需要區分「版本」概念
3. ✅ 所有 prompts 平等存取
4. ✅ 支援動態新增/修改
5. ✅ 更好的 UI 支援

## 疑難排解

### 問題 1: 找不到 prompt

**症狀**：`⚠️ 找不到 prompt 'xxx'，使用預設 prompt`

**解決**：
- 檢查 prompt 名稱拼寫
- 使用 `pm.list_prompts()` 查看可用的 prompts
- 預設會自動使用 default prompt，不會報錯

### 問題 2: Streamlit UI 無法啟動

**解決**：
```bash
# 安裝 streamlit
pip install streamlit

# 確認安裝
streamlit --version
```

### 問題 3: 配置文件未更新

**解決**：
- 確認 `save_to_file=True`
- 檢查文件寫入權限
- 查看終端輸出的錯誤訊息

## 版本歷史

- **v3.0** (2025-11-13) - 簡化版發布
  - 移除複雜的版本管理
  - 統一使用 prompt_name
  - 新增 Streamlit UI
  - 簡化 API

- **v2.0** (2025-11-13) - YAML 配置支援
- **v1.0** (2025-11-13) - 初始版本

## 相關文件

- [ui/README.md](ui/README.md) - Streamlit UI 文檔
- [example.py](example.py) - 使用範例
- [manager.py](manager.py) - 核心實作

## 授權

與專案主體相同
