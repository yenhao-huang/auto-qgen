#!/bin/bash

# 啟動 Streamlit 應用

# 設定工作目錄
cd "$(dirname "$0")"

# 檢查是否安裝 streamlit
if ! command -v streamlit &> /dev/null; then
    echo "⚠️  未安裝 streamlit"
    echo "請執行: pip install streamlit"
    exit 1
fi

# 啟動應用
echo "🚀 啟動 Prompt Manager UI..."
streamlit run app.py
