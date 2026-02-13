"""
LLM 客户端工厂
根据配置创建对应的客户端实例
"""
from typing import Dict, Optional
from .base import LLMClient, ModelConfig
from .deepseek_provider import DeepSeekClient
from .ollama_provider import OllamaClient


class LLMClientFactory:
    """LLM 客户端工厂"""

    _providers: Dict[str, type] = {
        'deepseek': DeepSeekClient,
        'ollama': OllamaClient
    }

    # 运行时配置缓存（用于切换模型）
    _runtime_config: Optional[ModelConfig] = None

    @classmethod
    def create_client(
        cls,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ) -> LLMClient:
        """创建 LLM 客户端实例

        Args:
            provider: 提供商 ('deepseek' | 'ollama')
            model_name: 模型名称
            api_key: API 密钥
            base_url: 自定义 base URL

        Returns:
            LLMClient 实例
        """
        # 如果有运行时配置，使用运行时配置
        if cls._runtime_config:
            config = cls._runtime_config
        else:
            # 使用配置或默认值
            config = cls._get_config(provider, model_name, api_key, base_url)

        # 创建对应客户端
        client_class = cls._providers.get(config.provider)
        if not client_class:
            raise ValueError(f"不支持的 LLM 提供商: {config.provider}")

        return client_class(config)

    @classmethod
    def _get_config(
        cls,
        provider: Optional[str],
        model_name: Optional[str],
        api_key: Optional[str],
        base_url: Optional[str]
    ) -> ModelConfig:
        """获取模型配置"""
        from config import Config

        # 使用默认提供商（从环境变量）
        if not provider:
            provider = getattr(Config, 'DEFAULT_LLM_PROVIDER', 'deepseek')

        # 确定模型名称
        if not model_name:
            model_name = cls._get_default_model(provider)

        # 确定是否支持推理
        if provider == 'deepseek':
            supports_reasoning = 'reasoner' in model_name
        elif provider == 'ollama':
            # Ollama 支持带思考能力的模型（仅 deepseek-r1 真正支持）
            thinking_models = ['deepseek-r1']
            model_lower = model_name.lower()
            supports_reasoning = any(tm in model_lower for tm in thinking_models)
        else:
            supports_reasoning = False

        # 获取 API key
        if not api_key:
            api_key = cls._get_api_key(provider)

        # 获取 base URL
        if not base_url:
            base_url = cls._get_base_url(provider)

        # 自动设置 enable_thinking：只有模型真正支持推理时才启用
        enable_thinking = supports_reasoning

        return ModelConfig(
            provider=provider,
            model_name=model_name,
            api_key=api_key,
            base_url=base_url,
            supports_reasoning=supports_reasoning,
            enable_thinking=enable_thinking
        )

    @classmethod
    def _get_default_model(cls, provider: str) -> str:
        """获取默认模型名称"""
        from config import Config

        defaults = {
            'deepseek': getattr(Config, 'DEEPSEEK_MODEL', 'deepseek-chat'),
            'ollama': getattr(Config, 'OLLAMA_MODEL', 'llama3.1')
        }
        return defaults.get(provider, 'deepseek-chat')

    @classmethod
    def _get_api_key(cls, provider: str) -> Optional[str]:
        """获取 API 密钥"""
        from config import Config

        if provider == 'deepseek':
            return getattr(Config, 'DEEPSEEK_API_KEY', None)
        elif provider == 'ollama':
            return 'ollama'  # Ollama 不需要真实 key

        return None

    @classmethod
    def _get_base_url(cls, provider: str) -> Optional[str]:
        """获取 base URL"""
        from config import Config

        if provider == 'deepseek':
            return 'https://api.deepseek.com'
        elif provider == 'ollama':
            return getattr(Config, 'OLLAMA_BASE_URL', 'http://localhost:11434')

        return None

    @classmethod
    def set_runtime_config(cls, provider: str, model: str, enable_thinking: bool = False):
        """设置运行时配置（用于模型切换）

        Args:
            provider: 提供商名称
            model: 模型名称
            enable_thinking: 是否启用 thinking 模式（仅 Ollama）
        """
        api_key = cls._get_api_key(provider)
        base_url = cls._get_base_url(provider)

        # 确定是否支持推理
        if provider == 'deepseek':
            supports_reasoning = 'reasoner' in model
        elif provider == 'ollama':
            # Ollama 支持带思考能力的模型（仅 deepseek-r1 真正支持）
            thinking_models = ['deepseek-r1']
            model_lower = model.lower()
            supports_reasoning = any(tm in model_lower for tm in thinking_models)
        else:
            supports_reasoning = False

        # 自动调整 enable_thinking：只有模型真正支持时才允许启用
        actual_enable_thinking = enable_thinking and supports_reasoning

        cls._runtime_config = ModelConfig(
            provider=provider,
            model_name=model,
            api_key=api_key,
            base_url=base_url,
            supports_reasoning=supports_reasoning,
            enable_thinking=actual_enable_thinking
        )

    @classmethod
    def clear_runtime_config(cls):
        """清除运行时配置（恢复默认）"""
        cls._runtime_config = None

    @classmethod
    def get_current_config(cls) -> Dict:
        """获取当前使用的配置"""
        from config import Config

        if cls._runtime_config:
            return {
                'provider': cls._runtime_config.provider,
                'model': cls._runtime_config.model_name,
                'supports_reasoning': cls._runtime_config.supports_reasoning,
                'enable_thinking': cls._runtime_config.enable_thinking
            }

        # 返回默认配置
        provider = getattr(Config, 'DEFAULT_LLM_PROVIDER', 'deepseek')

        if provider == 'deepseek':
            return {
                'provider': 'deepseek',
                'model': getattr(Config, 'DEEPSEEK_MODEL', 'deepseek-chat'),
                'supports_reasoning': 'reasoner' in getattr(Config, 'DEEPSEEK_MODEL', 'deepseek-chat'),
                'enable_thinking': False
            }
        elif provider == 'ollama':
            ollama_model = getattr(Config, 'OLLAMA_MODEL', 'llama3.1')
            thinking_models = ['deepseek-r1']
            supports_reasoning = any(tm in ollama_model.lower() for tm in thinking_models)
            return {
                'provider': 'ollama',
                'model': ollama_model,
                'supports_reasoning': supports_reasoning,
                'enable_thinking': False
            }

        return {
            'provider': 'deepseek',
            'model': 'deepseek-chat',
            'supports_reasoning': False,
            'enable_thinking': False
        }
