"""
DeepSeek LLM 提供商实现
支持 deepseek-chat 和 deepseek-reasoner
"""
from openai import OpenAI
from typing import Optional
from .base import LLMClient, ModelConfig


class DeepSeekClient(LLMClient):
    """DeepSeek API 客户端"""

    DEFAULT_MODELS = {
        'deepseek-chat': 'deepseek-chat',
        'deepseek-reasoner': 'deepseek-reasoner'
    }

    def __init__(self, config: ModelConfig):
        self.config = config
        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url or "https://api.deepseek.com"
        )

    def chat_completion(self, messages, model, think=False, **kwargs):
        """创建聊天完成（支持推理模式）

        Args:
            messages: 聊天消息列表
            model: 模型名称
            think: 是否启用思考模式（仅Ollama支持，DeepSeek忽略此参数）
            **kwargs: 其他参数
        """
        # DeepSeek API 不支持 think 参数，该参数仅用于接口兼容
        # Ollama 使用此参数启用思考模式，DeepSeek 则忽略
        _ = think  # 标记为已使用以抑制 linting 警告
        return self.client.chat.completions.create(
            model=model or self.config.model_name,
            messages=messages,
            **kwargs
        )

    def supports_reasoning_content(self) -> bool:
        """DeepSeek Reasoner 支持推理内容"""
        return 'reasoner' in self.config.model_name

    def get_reasoning_field_name(self) -> str:
        """DeepSeek API 使用 'reasoning_content' 字段"""
        return 'reasoning_content'
