"""Agent Chat 模块 - 兼容现有 UI 的 Agent 适配器"""
from typing import Dict, Generator, List, Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from core.agent import PetAgent
    from core.persona import PersonaManager


class AgentChatService:
    """
    Agent 聊天服务适配器
    
    将 LangChain Agent 包装为与现有 ChatService 兼容的接口，
    使得 UI 层无需修改即可使用 Agent 功能。
    """
    
    def __init__(
        self,
        agent: "PetAgent",
        persona_manager: "PersonaManager"
    ):
        """
        初始化 Agent 聊天服务
        
        Args:
            agent: PetAgent 实例
            persona_manager: PersonaManager 实例
        """
        self.agent = agent
        self.persona_manager = persona_manager
        self._context_limit = 128000
    
    def chat(self, messages: list) -> str:
        """
        发送消息并获取回复
        
        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            
        Returns:
            AI 回复文本
        """
        # 分离系统消息和对话历史
        history = []
        user_message = ""
        
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            if role == "user":
                user_message = content
            elif role in ("assistant", "system"):
                history.append(msg)
        
        if not user_message:
            return ""
        
        return self.agent.chat(user_message, history)
    
    def chat_stream(self, messages: list) -> Generator[str, None, None]:
        """
        流式发送消息并获取回复
        
        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            
        Yields:
            AI 回复文本片段
        """
        # 分离系统消息和对话历史
        history = []
        user_message = ""
        
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            if role == "user":
                user_message = content
            elif role in ("assistant", "system"):
                history.append(msg)
        
        if not user_message:
            return
        
        yield from self.agent.chat_stream(user_message, history)
    
    def count_tokens(self, messages: list) -> int:
        """
        计算消息的 token 数（估算）
        
        Args:
            messages: 消息列表
            
        Returns:
            token 数量
        """
        import tiktoken
        
        try:
            encoding = tiktoken.encoding_for_model(self.agent.config.model)
        except KeyError:
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
        """
        更新配置
        
        Args:
            config: 配置字典
        """
        from core.agent import AgentConfig
        
        api_config = config.get("api", {})
        agent_config = AgentConfig.from_dict(api_config)
        self.agent.update_config(agent_config)
        
        chat_config = config.get("chat", {})
        self._context_limit = chat_config.get("context_limit", 128000)
    
    def reload_skills(self):
        """重新加载技能"""
        skills = self.persona_manager.get_skills()
        self.agent.load_skills(skills)


class AgentChatFactory:
    """
    Agent 聊天服务工厂
    
    用于创建和配置 Agent 聊天服务实例
    """
    
    @staticmethod
    def create(
        config: dict,
        persona_manager: "PersonaManager"
    ) -> AgentChatService:
        """
        创建 Agent 聊天服务
        
        Args:
            config: 配置字典
            persona_manager: PersonaManager 实例
            
        Returns:
            AgentChatService 实例
        """
        from core.agent import PetAgent, AgentConfig
        
        # 创建 Agent 配置
        api_config = config.get("api", {})
        agent_config = AgentConfig.from_dict(api_config)
        
        # 创建 Agent
        agent = PetAgent(
            config=agent_config,
            name=persona_manager.name,
            system_prompt=persona_manager.system_prompt
        )
        
        # 链式加载技能
        if persona_manager.skills_enabled:
            skill_loader = persona_manager.get_skill_loader()
            skills = skill_loader.build()
            agent.load_skills(skills)
        
        return AgentChatService(agent, persona_manager)
    
    @staticmethod
    def create_with_handlers(
        config: dict,
        persona_manager: "PersonaManager",
        handlers: Dict[str, callable]
    ) -> AgentChatService:
        """
        创建带自定义处理器的 Agent 聊天服务
        
        Args:
            config: 配置字典
            persona_manager: PersonaManager 实例
            handlers: 处理器字典 {skill_name: handler}
            
        Returns:
            AgentChatService 实例
        """
        from core.agent import PetAgent, AgentConfig
        
        # 创建 Agent 配置
        api_config = config.get("api", {})
        agent_config = AgentConfig.from_dict(api_config)
        
        # 创建 Agent
        agent = PetAgent(
            config=agent_config,
            name=persona_manager.name,
            system_prompt=persona_manager.system_prompt
        )
        
        # 链式加载技能（带处理器）
        if persona_manager.skills_enabled:
            skill_loader = persona_manager.get_skill_loader()
            skills = skill_loader.build()
            agent.load_skills(skills, handlers)
        
        return AgentChatService(agent, persona_manager)


def create_agent_chat_service(
    config: dict,
    persona_manager: "PersonaManager",
    use_agent: bool = True,
    handlers: Optional[Dict[str, callable]] = None
) -> Any:
    """
    快捷函数：创建聊天服务
    
    根据配置选择使用 Agent 模式或传统模式
    
    Args:
        config: 配置字典
        persona_manager: PersonaManager 实例
        use_agent: 是否使用 Agent 模式
        handlers: 可选的处理器字典
        
    Returns:
        聊天服务实例
    """
    if use_agent:
        if handlers:
            return AgentChatFactory.create_with_handlers(
                config, persona_manager, handlers
            )
        return AgentChatFactory.create(config, persona_manager)
    else:
        # 传统模式
        from core.chat import ChatService
        return ChatService(config)
