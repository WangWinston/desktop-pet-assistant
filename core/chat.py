"""聊天服务模块 - OpenAI API 调用"""
from typing import Optional, Generator

from openai import OpenAI

from utils.config_loader import ConfigLoader


class ChatError(Exception):
    """聊天错误"""

    pass


class ChatService:
    """OpenAI 兼容 API 聊天服务"""

    def __init__(self, config: dict = None):
        if config is None:
            config = ConfigLoader.load()

        api_config = config.get("api", {})
        self.client = OpenAI(
            base_url=api_config.get("base_url", "https://api.openai.com/v1"),
            api_key=api_config.get("api_key", ""),
        )
        self.model = api_config.get("model", "gpt-4o-mini")
        self.max_tokens = api_config.get("max_tokens", 2048)
        self.temperature = config.get("chat", {}).get("temperature", 0.7)
        self._context_limit = config.get("chat", {}).get("context_limit", 128000)

    def chat(self, messages: list) -> str:
        """
        发送消息并获取回复

        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]

        Returns:
            AI 回复文本

        Raises:
            ChatError: API 调用失败
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise ChatError(f"API 调用失败: {str(e)}")

    def chat_stream(self, messages: list) -> Generator[str, None, None]:
        """
        流式发送消息并获取回复

        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]

        Yields:
            AI 回复文本片段

        Raises:
            ChatError: API 调用失败
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=True,
            )
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            raise ChatError(f"API 调用失败: {str(e)}")

    def count_tokens(self, messages: list) -> int:
        """
        计算消息的 token 数

        Args:
            messages: 消息列表

        Returns:
            token 数量
        """
        import tiktoken

        try:
            encoding = tiktoken.encoding_for_model(self.model)
        except KeyError:
            # 未知模型使用 cl100k_base
            encoding = tiktoken.get_encoding("cl100k_base")

        total = 0
        for msg in messages:
            total += 4  # 消息格式开销
            total += len(encoding.encode(msg.get("content", "")))
        return total

    def get_context_limit(self) -> int:
        """获取上下文限制"""
        return self._context_limit

    def update_config(self, config: dict):
        """更新配置"""
        api_config = config.get("api", {})
        self.client = OpenAI(
            base_url=api_config.get("base_url", "https://api.openai.com/v1"),
            api_key=api_config.get("api_key", ""),
        )
        self.model = api_config.get("model", "gpt-4o-mini")
        self.max_tokens = api_config.get("max_tokens", 2048)
        self.temperature = config.get("chat", {}).get("temperature", 0.7)
        self._context_limit = config.get("chat", {}).get("context_limit", 128000)