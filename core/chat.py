"""聊天服务模块 - OpenAI API 调用"""
from typing import Optional, Generator, Dict, Any, TYPE_CHECKING

from openai import OpenAI

from utils.config_loader import ConfigLoader
from utils.logger import get_logger

if TYPE_CHECKING:
    from core.persona import PersonaManager

# 模块日志
log = get_logger("chat")


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
        
        # Agent 模式支持
        self._use_agent = config.get("agent", {}).get("enabled", False)
        self._agent_service = None
        
        log.info(f"ChatService 初始化完成, model={self.model}, base_url={api_config.get('base_url')}")

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
        # 如果启用了 Agent 模式，使用 Agent 服务
        if self._use_agent and self._agent_service:
            log.debug("使用 Agent 模式处理消息")
            return self._agent_service.chat(messages)
        
        log.debug(f"发送消息, 消息数量={len(messages)}")
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            result = response.choices[0].message.content
            log.debug(f"收到回复, 长度={len(result)}")
            return result
        except Exception as e:
            log.error(f"API 调用失败: {str(e)}")
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
        # 如果启用了 Agent 模式，使用 Agent 服务
        if self._use_agent and self._agent_service:
            log.debug("使用 Agent 模式流式处理消息")
            yield from self._agent_service.chat_stream(messages)
            return
        
        log.debug(f"流式发送消息, 消息数量={len(messages)}")
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=True,
            )
            chunk_count = 0
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    chunk_count += 1
                    yield chunk.choices[0].delta.content
            log.debug(f"流式响应完成, chunks={chunk_count}")
        except Exception as e:
            log.error(f"API 调用失败: {str(e)}")
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
        
        # 更新 Agent 模式配置
        self._use_agent = config.get("agent", {}).get("enabled", False)
        
        # 如果有 Agent 服务，也更新它
        if self._agent_service:
            self._agent_service.update_config(config)
    
    def enable_agent_mode(
        self,
        persona_manager: "PersonaManager",
        handlers: Optional[Dict[str, Any]] = None
    ):
        """
        启用 Agent 模式
        
        Args:
            persona_manager: PersonaManager 实例
            handlers: 可选的技能处理器字典
        """
        from core.agent_chat import create_agent_chat_service
        
        log.info("启用 Agent 模式...")
        self._use_agent = True
        
        # 获取 API 配置（确保是字符串类型）
        api_key = getattr(self.client, 'api_key', None)
        base_url = str(getattr(self.client, 'base_url', 'https://api.openai.com/v1'))
        
        if not api_key:
            log.warning("API Key 未设置，Agent 模式可能无法正常工作")
        
        self._agent_service = create_agent_chat_service(
            config={
                "api": {
                    "api_key": api_key or "",
                    "base_url": base_url,
                    "model": self.model,
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                }
            },
            persona_manager=persona_manager,
            use_agent=True,
            handlers=handlers
        )
        log.info(f"Agent 模式已启用, 已加载 {len(self._agent_service.agent.tools)} 个工具")
    
    def disable_agent_mode(self):
        """禁用 Agent 模式"""
        self._use_agent = False
        self._agent_service = None
    
    @property
    def is_agent_mode(self) -> bool:
        """是否处于 Agent 模式"""
        return self._use_agent and self._agent_service is not None


def create_chat_service(
    config: dict,
    persona_manager: Optional["PersonaManager"] = None,
    use_agent: bool = False,
    handlers: Optional[Dict[str, Any]] = None
) -> ChatService:
    """
    工厂函数：创建聊天服务
    
    根据参数选择使用传统模式或 Agent 模式
    
    Args:
        config: 配置字典
        persona_manager: PersonaManager 实例（Agent 模式必需）
        use_agent: 是否使用 Agent 模式
        handlers: 可选的技能处理器字典
        
    Returns:
        ChatService 实例
    """
    service = ChatService(config)
    
    if use_agent and persona_manager:
        service.enable_agent_mode(persona_manager, handlers)
    
    return service