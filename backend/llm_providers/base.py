"""
LLM 客户端基类和接口定义
"""
from abc import ABC, abstractmethod
from typing import Optional, Callable
from dataclasses import dataclass


@dataclass
class ModelConfig:
    """模型配置"""
    provider: str  # 'deepseek' | 'ollama'
    model_name: str  # 'deepseek-chat', 'llama3.1', etc.
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    supports_reasoning: bool = False  # 是否支持推理内容
    enable_thinking: bool = False  # 是否启用 thinking 模式（仅 Ollama）


class LLMClient(ABC):
    """LLM 客户端抽象基类"""

    @abstractmethod
    def chat_completion(
        self,
        messages: list,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False,
        think: bool = False  # 新增：启用 thinking 模式（仅 Ollama）
    ):
        """创建聊天完成"""
        pass

    @abstractmethod
    def supports_reasoning_content(self) -> bool:
        """是否支持推理内容"""
        pass

    def get_reasoning_field_name(self) -> str:
        """获取思考内容的字段名

        不同提供商使用不同的字段名：
        - DeepSeek API: reasoning_content
        - Ollama API: thinking
        - 智谱 GLM API: reasoning_content

        Returns:
            str: 字段名，默认为 'reasoning_content'
        """
        return 'reasoning_content'
