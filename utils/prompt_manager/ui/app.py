#!/usr/bin/env python3
"""
Streamlit UI for Prompt Manager
提供視覺化介面來管理 prompts
"""

import streamlit as st
import sys
import os

# 添加父目錄到路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from manager import PromptManager, PromptConfig

# 頁面配置
st.set_page_config(
    page_title="Prompt Manager",
    page_icon="📝",
    layout="wide"
)

# 初始化 session state
if 'pm' not in st.session_state:
    st.session_state.pm = PromptManager()
if 'selected_prompt' not in st.session_state:
    st.session_state.selected_prompt = None


def main():
    st.title("📝 Prompt Manager")
    st.markdown("管理您的 LLM Prompts")

    # 側邊欄 - 功能選單
    with st.sidebar:
        st.header("功能選單")
        page = st.radio(
            "選擇功能",
            ["📋 查看 Prompts", "➕ 新增 Prompt", "✏️ 編輯 Prompt", "🗑️ 刪除 Prompt", "🧪 測試 Prompt"],
            label_visibility="collapsed"
        )

    # 主要內容區域
    if page == "📋 查看 Prompts":
        show_prompts_page()
    elif page == "➕ 新增 Prompt":
        add_prompt_page()
    elif page == "✏️ 編輯 Prompt":
        edit_prompt_page()
    elif page == "🗑️ 刪除 Prompt":
        delete_prompt_page()
    elif page == "🧪 測試 Prompt":
        test_prompt_page()


def show_prompts_page():
    """查看所有 prompts"""
    st.header("📋 所有 Prompts")

    prompts = st.session_state.pm.list_prompts()

    if not prompts:
        st.warning("目前沒有任何 prompts")
        return

    # 顯示 prompts 數量
    st.info(f"總共 {len(prompts)} 個 prompts")

    # 選擇要查看的 prompt
    selected = st.selectbox("選擇 Prompt", prompts)

    if selected:
        config = st.session_state.pm.get_prompt(selected)

        # 顯示 prompt 詳細資訊
        col1, col2 = st.columns([1, 2])

        with col1:
            st.subheader("基本資訊")
            st.text_input("Prompt 名稱", value=config.prompt_name, disabled=True)

        with col2:
            st.subheader("系統角色")
            st.text_area("System Role", value=config.system_role, height=100, disabled=True)

        st.subheader("任務描述")
        st.text_area("Task", value=config.task, height=100, disabled=True)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("要求")
            for i, req in enumerate(config.requirements, 1):
                st.text(f"{i}. {req}")

        with col2:
            st.subheader("輸出格式")
            for fmt in config.output_formats:
                st.text(fmt)

        if config.demonstrations:
            st.subheader("示範範例")
            for demo in config.demonstrations:
                st.code(demo)


def add_prompt_page():
    """新增 prompt"""
    st.header("➕ 新增 Prompt")

    # 取得 default prompt 作為預設值
    default_config = st.session_state.pm.get_prompt("default")

    # 選項：是否以 default 為基礎
    use_default = st.checkbox("以 Default Prompt 為基礎", value=True, help="勾選後會自動填入 default prompt 的內容")

    with st.form("add_prompt_form"):
        prompt_name = st.text_input(
            "Prompt 名稱 *",
            placeholder="例如：medical_expert",
            help="唯一識別符，建議使用英文和底線"
        )

        system_role = st.text_area(
            "系統角色 *",
            value=default_config.system_role if use_default else "",
            placeholder="例如：你是一位醫療資料分析專家。",
            height=100
        )

        task = st.text_area(
            "任務描述 *",
            value=default_config.task if use_default else "",
            placeholder="例如：請根據以下資料，生成查詢句子...",
            height=150
        )

        st.subheader("要求列表")
        default_reqs_count = len(default_config.requirements) if use_default else 3
        num_requirements = st.number_input("要求數量", min_value=1, max_value=10, value=default_reqs_count)

        requirements = []
        for i in range(num_requirements):
            default_value = default_config.requirements[i] if use_default and i < len(default_config.requirements) else ""
            req = st.text_input(f"要求 {i+1}", value=default_value, key=f"req_{i}")
            if req:
                requirements.append(req)

        st.subheader("輸出格式")
        default_fmt_count = len(default_config.output_formats) if use_default else 5
        num_outputs = st.number_input("輸出格式數量", min_value=1, max_value=10, value=default_fmt_count)

        output_formats = []
        for i in range(num_outputs):
            if use_default and i < len(default_config.output_formats):
                default_value = default_config.output_formats[i]
            else:
                default_value = f"{i+1}. [第{['一','二','三','四','五','六','七','八','九','十'][i]}個查詢句子]" if i < 10 else f"{i+1}. [查詢句子]"

            fmt = st.text_input(
                f"格式 {i+1}",
                value=default_value,
                key=f"fmt_{i}"
            )
            if fmt:
                output_formats.append(fmt)

        st.subheader("示範範例（可選）")
        default_demo_text = '\n'.join(default_config.demonstrations) if use_default and default_config.demonstrations else ""
        demonstrations_text = st.text_area(
            "示範",
            value=default_demo_text,
            placeholder="每行一個示範範例",
            height=100
        )
        demonstrations = [d.strip() for d in demonstrations_text.split('\n') if d.strip()] if demonstrations_text else None

        submitted = st.form_submit_button("新增 Prompt", type="primary")

        if submitted:
            if not prompt_name:
                st.error("請輸入 Prompt 名稱")
            elif not system_role:
                st.error("請輸入系統角色")
            elif not task:
                st.error("請輸入任務描述")
            elif not requirements:
                st.error("請至少添加一個要求")
            elif not output_formats:
                st.error("請至少添加一個輸出格式")
            else:
                try:
                    st.session_state.pm.add_prompt(
                        prompt_name=prompt_name,
                        system_role=system_role,
                        task=task,
                        requirements=requirements,
                        output_formats=output_formats,
                        demonstrations=demonstrations,
                        save_to_file=True
                    )
                    st.success(f"✓ 已成功新增 prompt: {prompt_name}")
                    st.balloons()
                except Exception as e:
                    st.error(f"新增失敗：{e}")


def edit_prompt_page():
    """編輯 prompt"""
    st.header("✏️ 編輯 Prompt")

    prompts = st.session_state.pm.list_prompts()

    if not prompts:
        st.warning("目前沒有任何 prompts 可以編輯")
        return

    selected = st.selectbox("選擇要編輯的 Prompt", prompts)

    if selected:
        config = st.session_state.pm.get_prompt(selected)

        with st.form("edit_prompt_form"):
            st.info(f"編輯: {config.prompt_name}")

            system_role = st.text_area(
                "系統角色",
                value=config.system_role,
                height=100
            )

            task = st.text_area(
                "任務描述",
                value=config.task,
                height=150
            )

            st.subheader("要求列表")
            requirements_text = st.text_area(
                "要求（每行一個）",
                value='\n'.join(config.requirements),
                height=150
            )
            requirements = [r.strip() for r in requirements_text.split('\n') if r.strip()]

            st.subheader("輸出格式")
            output_formats_text = st.text_area(
                "輸出格式（每行一個）",
                value='\n'.join(config.output_formats),
                height=150
            )
            output_formats = [f.strip() for f in output_formats_text.split('\n') if f.strip()]

            st.subheader("示範範例（可選）")
            demonstrations_text = st.text_area(
                "示範（每行一個）",
                value='\n'.join(config.demonstrations) if config.demonstrations else "",
                height=100
            )
            demonstrations = [d.strip() for d in demonstrations_text.split('\n') if d.strip()] if demonstrations_text else None

            submitted = st.form_submit_button("更新 Prompt", type="primary")

            if submitted:
                try:
                    st.session_state.pm.update_prompt(
                        prompt_name=selected,
                        system_role=system_role,
                        task=task,
                        requirements=requirements,
                        output_formats=output_formats,
                        demonstrations=demonstrations,
                        save_to_file=True
                    )
                    st.success(f"✓ 已成功更新 prompt: {selected}")
                    st.balloons()
                except Exception as e:
                    st.error(f"更新失敗：{e}")


def delete_prompt_page():
    """刪除 prompt"""
    st.header("🗑️ 刪除 Prompt")

    prompts = st.session_state.pm.list_prompts()

    if not prompts:
        st.warning("目前沒有任何 prompts 可以刪除")
        return

    # 過濾掉 default prompt
    deletable_prompts = [p for p in prompts if p != "default"]

    if not deletable_prompts:
        st.warning("沒有可刪除的 prompts（default prompt 無法刪除）")
        return

    selected = st.selectbox("選擇要刪除的 Prompt", deletable_prompts)

    if selected:
        config = st.session_state.pm.get_prompt(selected)

        st.warning("⚠️ 此操作無法復原！")

        # 顯示要刪除的 prompt 資訊
        with st.expander("查看 Prompt 內容"):
            st.text(f"名稱: {config.prompt_name}")
            st.text(f"系統角色: {config.system_role[:100]}...")
            st.text(f"任務: {config.task[:100]}...")

        if st.button("確認刪除", type="primary"):
            try:
                st.session_state.pm.delete_prompt(selected, save_to_file=True)
                st.success(f"✓ 已成功刪除 prompt: {selected}")
                st.rerun()
            except Exception as e:
                st.error(f"刪除失敗：{e}")


def test_prompt_page():
    """測試 prompt 生成"""
    st.header("🧪 測試 Prompt")

    prompts = st.session_state.pm.list_prompts()

    if not prompts:
        st.warning("目前沒有任何 prompts 可以測試")
        return

    selected = st.selectbox("選擇 Prompt", prompts)

    st.subheader("輸入背景資訊")
    context = st.text_area(
        "背景資訊",
        placeholder="例如：\n項目名稱：累計預算數\n年度：112年\n金額：714.6百萬元",
        height=150
    )

    if st.button("生成 Prompt", type="primary"):
        if not context:
            st.error("請輸入背景資訊")
        else:
            try:
                prompt_text = st.session_state.pm.generate_prompt_text(
                    prompt_name=selected,
                    context=context
                )

                st.subheader("生成的 Prompt")
                st.code(prompt_text, language="text")

                # 顯示字數統計
                st.info(f"總字數：{len(prompt_text)} 字元")

            except Exception as e:
                st.error(f"生成失敗：{e}")


if __name__ == "__main__":
    main()
