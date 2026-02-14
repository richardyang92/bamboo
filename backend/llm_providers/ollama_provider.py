"""
Ollama LLM 提供商实现（使用官方 SDK）
支持 llama3, mistral, codellama, qwen2.5, deepseek-r1 等本地模型

官方 SDK 文档: https://github.com/ollama/ollama-python
API 响应格式:
- ChatResponse: model, created_at, message, done, prompt_eval_count, eval_count
- Stream chunk: 相同字段，但 message.content 逐步返回，done=True 时包含完整统计
"""
import time
from datetime import datetime
from typing import Iterator, Optional
from dataclasses import dataclass
from .base import LLMClient, ModelConfig


@dataclass
class ChatMessage:
    """聊天消息"""
    role: str
    content: str
    thinking: Optional[str] = None  # 推理内容（如 deepseek-r1）


@dataclass
class Choice:
    """API 响应选项"""
    index: int
    message: ChatMessage
    finish_reason: Optional[str] = None


@dataclass
class Delta:
    """流式响应增量"""
    role: Optional[str] = None
    content: Optional[str] = None
    thinking: Optional[str] = None


@dataclass
class StreamChoice:
    """流式响应选项"""
    index: int
    delta: Delta
    finish_reason: Optional[str] = None


@dataclass
class Usage:
    """Token 使用情况"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class ChatCompletionResponse:
    """聊天完成响应（兼容 OpenAI 格式）"""
    id: str
    object: str
    created: int
    model: str
    choices: list[Choice]
    usage: Optional[Usage] = None


@dataclass
class StreamChunk:
    """流式响应块（兼容 OpenAI 格式）"""
    id: str
    object: str
    created: int
    model: str
    choices: list[StreamChoice]


def get_ollama_model_capabilities(model_name: str, base_url: str = "http://localhost:11434") -> dict:
    """获取 Ollama 模型的能力信息

    通过 client.show() 方法获取模型的 capabilities，判断是否支持思考模式等。

    Args:
        model_name: 模型名称
        base_url: Ollama 服务地址

    Returns:
        包含能力信息的字典:
        {
            'supports_thinking': bool,  # 是否支持思考/推理模式
            'capabilities': list,       # 完整的能力列表
            'details': dict             # 模型详情（family, parameter_size 等）
        }
    """
    result = {
        'supports_thinking': False,
        'capabilities': [],
        'details': {}
    }

    try:
        from ollama import Client
        client = Client(host=base_url)

        # 使用 show() 方法获取模型信息
        info = client.show(model_name)

        # 获取 capabilities 列表
        capabilities = getattr(info, 'capabilities', None)
        if capabilities is None:
            # 尝试从 dict 格式获取
            capabilities = info.get('capabilities', []) if isinstance(info, dict) else []

        result['capabilities'] = list(capabilities) if capabilities else []

        # 检查是否支持思考模式
        result['supports_thinking'] = 'thinking' in result['capabilities']

        # 获取模型详情
        details = getattr(info, 'details', None)
        if details is None:
            details = info.get('details', {}) if isinstance(info, dict) else {}
        result['details'] = details if isinstance(details, dict) else {}

        print(f"[DEBUG] 模型 {model_name} capabilities: {result['capabilities']}, supports_thinking: {result['supports_thinking']}")

    except ImportError:
        print("[WARNING] ollama SDK 未安装，无法获取模型能力信息")
    except Exception as e:
        print(f"[WARNING] 获取模型 {model_name} 能力信息失败: {e}")
        # 回退到硬编码的推理模型列表
        reasoning_models = ['deepseek-r1', 'deepseek-v3', 'qwen3', 'phi-4']
        model_lower = model_name.lower()
        result['supports_thinking'] = any(rm in model_lower for rm in reasoning_models)

    return result


class OllamaClient(LLMClient):
    """Ollama 本地模型客户端（使用官方 SDK）"""

    DEFAULT_MODELS = {
        'deepseek-ocr': 'deepseek-ocr:latest',
        'deepseek-r1': 'deepseek-r1:latest',
        'qwen3-vl': 'qwen3-vl:8b',
        'qwen3-coder-next': 'qwen3-coder-next:latest',
        'gpt-oss': 'gpt-oss:20b',
        'glm-4.7-flash': 'glm-4.7-flash:latest'
    }

    @staticmethod
    def _parse_created_at(created_at_value) -> int:
        """将 Ollama 返回的 created_at 转换为 Unix 时间戳

        Args:
            created_at_value: 可能是 ISO 格式字符串、整数或 None

        Returns:
            Unix 时间戳（整数）
        """
        if isinstance(created_at_value, int):
            return created_at_value

        if isinstance(created_at_value, str):
            try:
                # 尝试解析 ISO 8601 格式时间戳
                dt = datetime.fromisoformat(created_at_value.replace('Z', '+00:00'))
                return int(dt.timestamp())
            except (ValueError, AttributeError):
                pass

        # 回退到当前时间
        return int(time.time())

    def __init__(self, config: ModelConfig):
        self.config = config
        self.base_url = config.base_url or "http://localhost:11434"

        # 导入官方 SDK（延迟导入，避免未安装时报错）
        try:
            from ollama import Client
            self._client = Client(host=self.base_url)
            self._is_available = True
        except ImportError as e:
            print("[ERROR] ollama SDK 未安装，请运行: pip install ollama")
            self._client = None
            self._is_available = False
        except Exception as e:
            print(f"[WARNING] Ollama 服务不可用: {e}")
            self._client = None
            self._is_available = False

        if not self._is_available:
            print("[INFO] 安装 Ollama: https://ollama.ai")
            print("[INFO] 启动 Ollama: ollama serve")

    def chat_completion(
        self,
        messages: list,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False,
        think: bool = False,  # 是否启用思考模式（推理模型如 deepseek-r1, qwen3）
        **kwargs
    ):
        """创建聊天完成（使用官方 SDK）

        Args:
            messages: 聊天消息列表
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大生成 tokens
            stream: 是否使用流式响应
            think: 是否启用思考模式（仅部分模型支持）
            **kwargs: 其他参数

        Returns:
            流式响应返回迭代器，非流式返回 ChatCompletionResponse
        """
        if not self._is_available or not self._client:
            raise RuntimeError("Ollama 客户端不可用，请确保 Ollama 已启动且 SDK 已安装")

        # 转换消息格式
        ollama_messages = [
            {'role': msg['role'], 'content': msg['content']}
            for msg in messages
        ]

        # 准备选项参数
        options = {
            'temperature': temperature,
            'num_predict': max_tokens
        }

        # 添加其他可选参数
        if 'top_p' in kwargs:
            options['top_p'] = kwargs['top_p']
        if 'frequency_penalty' in kwargs:
            options['frequency_penalty'] = kwargs['frequency_penalty']
        if 'presence_penalty' in kwargs:
            options['presence_penalty'] = kwargs['presence_penalty']

        # 模型名称
        model_name = model or self.config.model_name

        # 只有当模型支持推理且用户启用时，才启用 think 模式
        actual_think = think and self.supports_reasoning_content()
        if think and not actual_think:
            print(f"[DEBUG] 模型 {model_name} 不支持 thinking 模式，将使用普通模式")

        if stream:
            # 流式响应
            return self._stream_completion(model_name, ollama_messages, options, actual_think)
        else:
            # 非流式响应
            return self._non_stream_completion(model_name, ollama_messages, options, actual_think)

    def _non_stream_completion(
        self,
        model: str,
        messages: list,
        options: dict,
        think: bool = False
    ) -> ChatCompletionResponse:
        """非流式聊天完成（使用官方 SDK）

        SDK 响应格式:
        - response.model: 模型名称
        - response.created_at: 创建时间
        - response.message.role: 'assistant'
        - response.message.content: 生成的内容
        - response.done: True
        - response.prompt_eval_count: 输入 token 数
        - response.eval_count: 输出 token 数
        """
        from ollama import ResponseError

        try:
            response = self._client.chat(
                model=model,
                messages=messages,
                options=options,
                think=think
            )

            # SDK 直接返回的 ChatResponse 对象，直接访问其属性
            message = ChatMessage(
                role=response.message.role or 'assistant',
                content=response.message.content or ''
            )

            # 检查是否有推理内容（deepseek-r1, qwen3 等模型）
            # 推理模型在 message 中包含 thinking 字段
            if hasattr(response.message, 'thinking'):
                message.thinking = response.message.thinking

            choice = Choice(
                index=0,
                message=message,
                finish_reason='stop'
            )

            # 提取 token 使用情况
            usage = None
            if hasattr(response, 'prompt_eval_count') and hasattr(response, 'eval_count'):
                usage = Usage(
                    prompt_tokens=response.prompt_eval_count or 0,
                    completion_tokens=response.eval_count or 0,
                    total_tokens=(response.prompt_eval_count or 0) + (response.eval_count or 0)
                )

            # 使用 SDK 返回的时间戳（可能是 ISO 格式字符串）
            created_at_value = getattr(response, 'created_at', None)
            created_at = self._parse_created_at(created_at_value)

            return ChatCompletionResponse(
                id=f'ollama-{created_at}',
                object='chat.completion',
                created=created_at,
                model=response.model or model,
                choices=[choice],
                usage=usage
            )

        except ResponseError as e:
            print(f"[ERROR] Ollama API 调用失败: {e}")
            raise RuntimeError(f"Ollama API 错误: {e}") from e
        except Exception as e:
            print(f"[ERROR] Ollama 调用失败: {e}")
            raise

    def _stream_completion(
        self,
        model: str,
        messages: list,
        options: dict,
        think: bool = False
    ) -> Iterator[StreamChunk]:
        """流式聊天完成（使用官方 SDK）

        流式响应格式:
        - 每个 chunk 包含: model, created_at, message, done
        - message.content: 逐步生成的文本片段
        - message.role: 通常只在第一个 chunk 返回
        - done=True: 表示最后一个 chunk，包含 prompt_eval_count 和 eval_count
        - 推理模型可能在 message 中包含 reasoning_content
        """
        from ollama import ResponseError

        try:
            stream = self._client.chat(
                model=model,
                messages=messages,
                options=options,
                stream=True,
                think=think
            )

            for chunk in stream:
                # SDK 返回的 ChatResponse 对象，直接访问属性
                delta = Delta()

                # 提取角色（通常在第一个 chunk）
                if hasattr(chunk.message, 'role') and chunk.message.role:
                    delta.role = chunk.message.role

                # 提取内容（流式逐步返回）
                if hasattr(chunk.message, 'content') and chunk.message.content:
                    delta.content = chunk.message.content

                # 检查是否有推理内容（deepseek-r1, qwen3 等模型）
                if hasattr(chunk.message, 'thinking') and chunk.message.thinking:
                    delta.thinking = chunk.message.thinking

                # 检查是否完成
                finish_reason = None
                if chunk.done:
                    finish_reason = 'stop'

                stream_choice = StreamChoice(
                    index=0,
                    delta=delta,
                    finish_reason=finish_reason
                )

                # 使用 SDK 返回的时间戳（可能是 ISO 格式字符串）
                created_at_value = getattr(chunk, 'created_at', None)
                created_at = self._parse_created_at(created_at_value)

                yield StreamChunk(
                    id=f'ollama-{created_at}',
                    object='chat.completion.chunk',
                    created=created_at,
                    model=chunk.model or model,
                    choices=[stream_choice]
                )

        except ResponseError as e:
            print(f"[ERROR] Ollama 流式 API 调用失败: {e}")
            raise RuntimeError(f"Ollama 流式 API 错误: {e}") from e
        except Exception as e:
            print(f"[ERROR] Ollama 流式调用失败: {e}")
            raise

    def supports_reasoning_content(self) -> bool:
        """检查模型是否支持推理内容（如 deepseek-r1 等）

        优先使用动态获取的 capabilities 判断，失败时回退到硬编码列表
        """
        model_name = self.config.model_name or ''
        if not model_name:
            return False

        # 尝试动态获取模型能力
        try:
            capabilities_info = get_ollama_model_capabilities(model_name, self.base_url)
            return capabilities_info.get('supports_thinking', False)
        except Exception:
            pass

        # 回退到硬编码的推理模型列表
        reasoning_models = [
            'deepseek-r1',
            'deepseek-r1:latest',
        ]

        model_lower = model_name.lower()
        return any(rm in model_lower for rm in reasoning_models)

    def get_reasoning_field_name(self) -> str:
        """Ollama SDK 推理内容字段名

        推理模型通常使用 'thinking' 字段
        """
        return 'thinking'
