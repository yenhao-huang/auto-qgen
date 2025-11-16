#!/usr/bin/env python3
"""
簡化版 Prompt Manager
使用者可以直接透過 prompt_name 新增和取得 prompt
"""

import os
import yaml
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class PromptConfig:
    """Prompt 配置結構"""
    prompt_name: str
    system_role: str
    task: str
    requirements: List[str]
    output_formats: List[str]
    demonstrations: Optional[List[str]] = None

    def to_dict(self) -> Dict:
        """轉換為字典"""
        return asdict(self)


class PromptManager:
    """
    簡化版 Prompt 管理器

    功能：
    1. 透過 prompt_name 新增 prompt
    2. 透過 prompt_name 取得 prompt
    3. 自動從 YAML 載入已存在的 prompts
    4. 找不到 prompt_name 時使用預設 prompt
    """

    def __init__(self, config_file: Optional[str] = None):
        """
        初始化 Prompt Manager

        Args:
            config_file: YAML 配置文件路徑（可選）
                        如果不提供，使用預設路徑 prompts_config.yml
        """
        if config_file is None:
            # 使用預設路徑
            config_file = os.path.join(
                os.path.dirname(__file__),
                "prompts_config.yml"
            )

        self.config_file = config_file
        self._prompts: Dict[str, PromptConfig] = {}

        # 載入現有配置
        if os.path.exists(config_file):
            self._load_from_yaml()
        else:
            # 如果配置文件不存在，創建預設 prompt
            self._create_default_prompts()

    def _load_from_yaml(self):
        """從 YAML 文件載入所有 prompts"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if not data:
                self._create_default_prompts()
                return

            # 載入所有 prompts
            for prompt_name, config in data.items():
                self._prompts[prompt_name] = PromptConfig(
                    prompt_name=prompt_name,
                    system_role=config.get('system_role', ''),
                    task=config.get('task', ''),
                    requirements=config.get('requirements', []),
                    output_formats=config.get('output_formats', []),
                    demonstrations=config.get('demonstrations', None)
                )

            print(f"✓ 已載入 {len(self._prompts)} 個 prompts")

        except Exception as e:
            print(f"⚠️  載入配置失敗：{e}")
            self._create_default_prompts()

    def _create_default_prompts(self):
        """創建預設 prompts"""
        default_prompt = PromptConfig(
            prompt_name="default",
            system_role="你是一位醫療資料分析專家。",
            task="請根據以下正式的醫療統計資料，生成3-5個不同的口語化查詢句子，這些句子是醫療專業人員可能會用來搜尋這項資料的自然語言問句。",
            requirements=[
                "生成的查詢句子要自然、口語化，符合醫療專業人員的表達習慣",
                "包含不同的問法和角度（如：總覽性問題、趨勢分析、比較性問題等）",
                "保持專業性但避免過於正式的官方用語",
                "每個句子都要能夠找到這筆資料作為答案",
                "句子長度適中，不要過長或過短"
            ],
            output_formats=[
                "1. [第一個查詢句子]",
                "2. [第二個查詢句子]",
                "3. [第三個查詢句子]",
                "4. [第四個查詢句子]",
                "5. [第五個查詢句子]"
            ],
            demonstrations=None
        )
        self._prompts["default"] = default_prompt

    def add_prompt(
        self,
        prompt_name: str,
        system_role: str,
        task: str,
        requirements: List[str],
        output_formats: List[str],
        demonstrations: Optional[List[str]] = None,
        save_to_file: bool = True
    ) -> None:
        """
        新增一個 prompt

        Args:
            prompt_name: Prompt 名稱（唯一識別符）
            system_role: 系統角色
            task: 任務描述
            requirements: 要求列表
            output_formats: 輸出格式範例
            demonstrations: 示範範例（可選）
            save_to_file: 是否儲存到配置文件（預設：True）
        """
        prompt_config = PromptConfig(
            prompt_name=prompt_name,
            system_role=system_role,
            task=task,
            requirements=requirements,
            output_formats=output_formats,
            demonstrations=demonstrations
        )

        self._prompts[prompt_name] = prompt_config

        if save_to_file:
            self._save_to_yaml()

        print(f"✓ 已新增 prompt: {prompt_name}")

    def get_prompt(self, prompt_name: str, use_default_if_not_found: bool = True) -> Optional[PromptConfig]:
        """
        取得指定名稱的 prompt

        Args:
            prompt_name: Prompt 名稱
            use_default_if_not_found: 找不到時是否使用預設 prompt（預設：True）

        Returns:
            PromptConfig: Prompt 配置，找不到且不使用預設時返回 None
        """
        if prompt_name in self._prompts:
            return self._prompts[prompt_name]

        if use_default_if_not_found:
            print(f"⚠️  找不到 prompt '{prompt_name}'，使用預設 prompt")
            return self._prompts.get("default")

        return None

    def generate_prompt_text(
        self,
        prompt_name: str,
        context: str,
        use_default_if_not_found: bool = True
    ) -> str:
        """
        根據 prompt_name 和輸入資料生成完整的 prompt 文字

        Args:
            prompt_name: Prompt 名稱
            context: 輸入資料（會插入到 prompt 中）
            use_default_if_not_found: 找不到時是否使用預設 prompt

        Returns:
            str: 完整的 prompt 文字
        """
        config = self.get_prompt(prompt_name, use_default_if_not_found)

        if config is None:
            raise ValueError(f"找不到 prompt '{prompt_name}' 且未啟用預設 prompt")

        # 組合 prompt
        parts = []

        # 系統角色
        parts.append(config.system_role)
        parts.append("")

        # 任務描述
        parts.append(config.task)
        parts.append("")

        # 輸入資料
        parts.append("輸入資料：")
        parts.append(context)
        parts.append("")

        # 要求
        if config.requirements:
            parts.append("要求：")
            for i, req in enumerate(config.requirements, 1):
                parts.append(f"{i}. {req}")
            parts.append("")

        # 示範（如果有）
        if config.demonstrations:
            parts.append("示範範例：")
            for demo in config.demonstrations:
                parts.append(demo)
            parts.append("")

        # 輸出格式
        if config.output_formats:
            parts.append("請用以下格式回應：")
            for fmt in config.output_formats:
                parts.append(fmt)

        return "\n".join(parts)

    def list_prompts(self) -> List[str]:
        """
        列出所有可用的 prompt 名稱

        Returns:
            List[str]: Prompt 名稱列表
        """
        return list(self._prompts.keys())

    def delete_prompt(self, prompt_name: str, save_to_file: bool = True) -> bool:
        """
        刪除指定的 prompt

        Args:
            prompt_name: Prompt 名稱
            save_to_file: 是否同步刪除配置文件中的內容

        Returns:
            bool: 是否刪除成功
        """
        if prompt_name == "default":
            print("⚠️  無法刪除預設 prompt")
            return False

        if prompt_name not in self._prompts:
            print(f"⚠️  找不到 prompt '{prompt_name}'")
            return False

        del self._prompts[prompt_name]

        if save_to_file:
            self._save_to_yaml()

        print(f"✓ 已刪除 prompt: {prompt_name}")
        return True

    def _save_to_yaml(self):
        """儲存所有 prompts 到 YAML 文件"""
        try:
            data = {}
            for prompt_name, config in self._prompts.items():
                data[prompt_name] = {
                    'system_role': config.system_role,
                    'task': config.task,
                    'requirements': config.requirements,
                    'output_formats': config.output_formats,
                }
                if config.demonstrations:
                    data['demonstrations'] = config.demonstrations

            # 確保目錄存在
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

            print(f"✓ 已儲存配置到 {self.config_file}")

        except Exception as e:
            print(f"⚠️  儲存配置失敗：{e}")

    def update_prompt(
        self,
        prompt_name: str,
        system_role: Optional[str] = None,
        task: Optional[str] = None,
        requirements: Optional[List[str]] = None,
        output_formats: Optional[List[str]] = None,
        demonstrations: Optional[List[str]] = None,
        save_to_file: bool = True
    ) -> bool:
        """
        更新現有的 prompt

        Args:
            prompt_name: Prompt 名稱
            system_role: 新的系統角色（可選）
            task: 新的任務描述（可選）
            requirements: 新的要求列表（可選）
            output_formats: 新的輸出格式（可選）
            demonstrations: 新的示範範例（可選）
            save_to_file: 是否儲存到配置文件

        Returns:
            bool: 是否更新成功
        """
        if prompt_name not in self._prompts:
            print(f"⚠️  找不到 prompt '{prompt_name}'")
            return False

        config = self._prompts[prompt_name]

        # 更新非 None 的欄位
        if system_role is not None:
            config.system_role = system_role
        if task is not None:
            config.task = task
        if requirements is not None:
            config.requirements = requirements
        if output_formats is not None:
            config.output_formats = output_formats
        if demonstrations is not None:
            config.demonstrations = demonstrations

        if save_to_file:
            self._save_to_yaml()

        print(f"✓ 已更新 prompt: {prompt_name}")
        return True


# ==================== 測試用例 ====================

if __name__ == "__main__":
    print("=" * 80)
    print("測試簡化版 PromptManager")
    print("=" * 80)

    # 測試 1: 初始化並載入預設配置
    print("\n【測試 1】初始化 PromptManager")
    print("-" * 80)
    pm = PromptManager()
    print(f"可用 prompts: {pm.list_prompts()}")

    # 測試 2: 新增自訂 prompt
    print("\n【測試 2】新增自訂 prompt")
    print("-" * 80)
    pm.add_prompt(
        prompt_name="my_custom_prompt",
        system_role="你是一位資深健保專家。",
        task="請生成專業的查詢句子。",
        requirements=[
            "使用專業術語",
            "保持簡潔",
            "關注數據"
        ],
        output_formats=[
            "1. [查詢 1]",
            "2. [查詢 2]",
            "3. [查詢 3]"
        ],
        demonstrations=["範例：112年的預算執行率是多少？"],
        save_to_file=False  # 測試時不儲存
    )
    print(f"可用 prompts: {pm.list_prompts()}")

    # 測試 3: 取得 prompt
    print("\n【測試 3】取得 prompt")
    print("-" * 80)
    config = pm.get_prompt("my_custom_prompt")
    print(f"Prompt 名稱: {config.prompt_name}")
    print(f"系統角色: {config.system_role}")
    print(f"任務: {config.task}")
    print(f"要求數量: {len(config.requirements)}")

    # 測試 4: 生成完整 prompt 文字
    print("\n【測試 4】生成完整 prompt 文字")
    print("-" * 80)
    context = "項目名稱：累計預算數\n年度：112年\n金額：714.6百萬元"
    prompt_text = pm.generate_prompt_text("my_custom_prompt", context)
    print(f"生成的 Prompt (前 300 字):\n{prompt_text[:300]}...")

    # 測試 5: 使用不存在的 prompt（自動使用預設）
    print("\n【測試 5】使用不存在的 prompt")
    print("-" * 80)
    config = pm.get_prompt("non_existent_prompt")
    print(f"返回的 prompt 名稱: {config.prompt_name}")

    # 測試 6: 更新 prompt
    print("\n【測試 6】更新 prompt")
    print("-" * 80)
    pm.update_prompt(
        "my_custom_prompt",
        system_role="你是一位超級資深的健保專家。",
        save_to_file=False
    )
    updated_config = pm.get_prompt("my_custom_prompt")
    print(f"更新後的系統角色: {updated_config.system_role}")

    print("\n" + "=" * 80)
    print("✓ 所有測試完成")
    print("=" * 80)
