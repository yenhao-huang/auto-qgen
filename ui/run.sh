#!/bin/bash
# 啟動 Web UI

echo "=== Auto-Gen MultiModel Web UI ==="
echo ""

# 檢查 gradio 是否已安裝
if ! python -c "import gradio" 2>/dev/null; then
    echo "安裝 gradio..."
    pip install gradio
fi

# 檢查 PIL 是否已安裝
if ! python -c "from PIL import Image" 2>/dev/null; then
    echo "安裝 pillow..."
    pip install pillow
fi

echo ""
echo "啟動 Web UI..."
echo "瀏覽器將自動打開，或手動訪問: http://localhost:7860"
echo ""

cd "$(dirname "$0")/.."
python ui/web_ui.py
