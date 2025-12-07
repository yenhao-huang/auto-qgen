import json


class PromptManager:
    def __init__(self, prompt_key: str, prompt_corpuse_path: str = "configs/prompt_corpus.json"):
        prompt_corpus = self._load_prompt_corpus(prompt_corpuse_path)
        self.prompt_template = prompt_corpus[prompt_key]

    def _load_prompt_corpus(self, prompt_corpuse_path):
        with open(prompt_corpuse_path, 'r', encoding='utf-8') as f:
            prompt_corpus = json.load(f)
        return prompt_corpus

    def generate_prompt_text(self, context: str):
        prompt = self.prompt_template.format(context=context)
        return prompt