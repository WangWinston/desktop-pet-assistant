"""LangChain Agent 模块 - 基于技能的智能代理"""
from typing import Any, Callable, Dict, List, Optional, Sequence, Generator, Union
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_core.tools import BaseTool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.callbacks import BaseCallbackHandler

from core.skill_tool import SkillToolChain, create_skill_tools


class StreamHandler(BaseCallbackHandler):
    """流式输出回调处理器"""
    
    def __init__(self, callback: Optional[Callable[[str], None]] = None):
        self.callback = callback
        self.tokens: List[str] = []
    
    def on_llm_new_token(self, token: str, **kwargs) -> None:
        """收到新 token"""
        self.tokens.append(token)
        if self.callback:
            self.callback(token)


class AgentConfig:
    """Agent 配置"""
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.extra = kwargs
    
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> "AgentConfig":
        """从字典创建配置"""
        return cls(
            api_key=config.get("api_key", ""),
            base_url=config.get("base_url", "https://api.openai.com/v1"),
            model=config.get("model", "gpt-4o-mini"),
            temperature=config.get("temperature", 0.7),
            max_tokens=config.get("max_tokens", 2048)
        )


class PetAgent:
    """
    桌面宠物 Agent
    
    基于 LangChain 的智能代理，支持：
    - 链式加载技能
    - 流式输出
    - 工具调用
    - 记忆管理
    """
    
    # 默认系统提示模板
    SYSTEM_TEMPLATE = """你是一个可爱的桌面宠物助手，你的名字是{name}。

{system_prompt}

你可以使用以下工具来帮助用户：
{tools_description}

当用户的问题涉及某个技能时，你应该调用相应的工具来提供帮助。
回复时请保持友好、活泼的语气。"""
    
    def __init__(
        self,
        config: AgentConfig,
        name: str = "皮卡丘",
        system_prompt: str = ""
    ):
        """
        初始化 Agent
        
        Args:
            config: Agent 配置
            name: 宠物名称
            system_prompt: 系统提示词
        """
        self.config = config
        self.name = name
        self.system_prompt = system_prompt
        self._tools: List[BaseTool] = []
        self._tool_chain: Optional[SkillToolChain] = None
        self._llm: Optional[ChatOpenAI] = None
        self._llm_with_tools: Optional[Any] = None
        self._messages: List[BaseMessage] = []
        
        self._init_llm()
    
    def _init_llm(self):
        """初始化 LLM"""
        self._llm = ChatOpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            model=self.config.model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            streaming=True
        )
        
        # 如果有工具，绑定到 LLM
        if self._tools:
            self._llm_with_tools = self._llm.bind_tools(self._tools)
        else:
            self._llm_with_tools = None
    
    @property
    def tools(self) -> List[BaseTool]:
        """获取已加载的工具列表"""
        return self._tools
    
    @property
    def tool_chain(self) -> SkillToolChain:
        """获取工具链（懒加载）"""
        if self._tool_chain is None:
            self._tool_chain = SkillToolChain()
        return self._tool_chain
    
    def load_skill(
        self,
        skill_info: Dict[str, Any],
        handler: Optional[Callable] = None
    ) -> "PetAgent":
        """
        链式加载单个技能
        
        Args:
            skill_info: 技能信息
            handler: 可选的处理器
            
        Returns:
            返回自身，支持链式调用
        """
        self.tool_chain.load(skill_info, handler)
        self._tools = self.tool_chain.build()
        self._rebuild_agent()
        return self
    
    def load_skills(
        self,
        skills: Dict[str, Dict[str, Any]],
        handlers: Optional[Dict[str, Callable]] = None
    ) -> "PetAgent":
        """
        链式加载多个技能
        
        Args:
            skills: 技能字典
            handlers: 可选的处理器字典
            
        Returns:
            返回自身，支持链式调用
        """
        self.tool_chain.load_batch(skills, handlers)
        self._tools = self.tool_chain.build()
        self._rebuild_agent()
        return self
    
    def load_skills_from_directory(
        self,
        directory: str,
        handlers: Optional[Dict[str, Callable]] = None
    ) -> "PetAgent":
        """
        从目录链式加载技能
        
        Args:
            directory: 技能目录路径
            handlers: 可选的处理器字典
            
        Returns:
            返回自身，支持链式调用
        """
        self.tool_chain.load_from_directory(directory, handlers)
        self._tools = self.tool_chain.build()
        self._rebuild_agent()
        return self
    
    def with_handler(
        self,
        skill_name: str,
        handler: Callable
    ) -> "PetAgent":
        """
        为技能设置处理器
        
        Args:
            skill_name: 技能名称
            handler: 处理器函数
            
        Returns:
            返回自身，支持链式调用
        """
        self.tool_chain.with_handler(skill_name, handler)
        self._tools = self.tool_chain.build()
        self._rebuild_agent()
        return self
    
    def clear_skills(self) -> "PetAgent":
        """
        清空所有技能
        
        Returns:
            返回自身，支持链式调用
        """
        self.tool_chain.clear()
        self._tools = []
        self._rebuild_agent()
        return self
    
    def _rebuild_agent(self):
        """重建 Agent（工具变化时调用）"""
        if self._llm is None:
            return
        
        # 如果有工具，绑定到 LLM
        if self._tools:
            self._llm_with_tools = self._llm.bind_tools(self._tools)
        else:
            self._llm_with_tools = None
    
    def _format_tools_description(self) -> str:
        """格式化工具描述"""
        if not self._tools:
            return "当前没有可用工具。"
        
        lines = []
        for tool in self._tools:
            lines.append(f"- {tool.name}: {tool.description}")
        return "\n".join(lines)
    
    def chat(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        发送消息并获取回复
        
        Args:
            message: 用户消息
            history: 历史消息列表
            
        Returns:
            AI 回复
        """
        # 转换历史消息
        chat_history = self._convert_history(history)
        
        # 构建消息列表
        tools_description = self._format_tools_description()
        system_content = self.SYSTEM_TEMPLATE.format(
            name=self.name,
            system_prompt=self.system_prompt,
            tools_description=tools_description
        )
        
        messages = [SystemMessage(content=system_content)] + chat_history + [HumanMessage(content=message)]
        
        # 使用带工具的 LLM 或普通 LLM
        llm_to_use = self._llm_with_tools if self._llm_with_tools else self._llm
        
        response = llm_to_use.invoke(messages)
        
        # 如果有工具调用，执行工具并获取最终响应
        if hasattr(response, 'tool_calls') and response.tool_calls:
            # 执行工具调用
            tool_messages = []
            for tool_call in response.tool_calls:
                tool_name = tool_call['name']
                tool_args = tool_call.get('args', {})
                
                # 查找并执行对应的工具
                for tool in self._tools:
                    if tool.name == tool_name:
                        try:
                            result = tool._run(
                                query=tool_args.get('query', ''),
                                context=tool_args.get('context', '')
                            )
                            tool_messages.append({
                                'role': 'tool',
                                'content': result,
                                'tool_call_id': tool_call.get('id', '')
                            })
                        except Exception as e:
                            tool_messages.append({
                                'role': 'tool',
                                'content': f"工具执行错误: {str(e)}",
                                'tool_call_id': tool_call.get('id', '')
                            })
                        break
            
            # 添加工具调用结果到消息，再次调用 LLM
            messages.append(response)
            for tm in tool_messages:
                from langchain_core.messages import ToolMessage
                messages.append(ToolMessage(
                    content=tm['content'],
                    tool_call_id=tm['tool_call_id']
                ))
            
            final_response = self._llm.invoke(messages)
            return final_response.content
        
        return response.content
    
    def chat_stream(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None
    ) -> Generator[str, None, None]:
        """
        流式发送消息并获取回复
        
        Args:
            message: 用户消息
            history: 历史消息列表
            
        Yields:
            AI 回复片段
        """
        # 转换历史消息
        chat_history = self._convert_history(history)
        
        # 构建消息列表
        tools_description = self._format_tools_description()
        system_content = self.SYSTEM_TEMPLATE.format(
            name=self.name,
            system_prompt=self.system_prompt,
            tools_description=tools_description
        )
        
        messages = [SystemMessage(content=system_content)] + chat_history + [HumanMessage(content=message)]
        
        # 使用带工具的 LLM 或普通 LLM
        llm_to_use = self._llm_with_tools if self._llm_with_tools else self._llm
        
        # 先检查是否有工具调用
        response = llm_to_use.invoke(messages)
        
        # 如果有工具调用，执行工具并获取最终响应
        if hasattr(response, 'tool_calls') and response.tool_calls:
            # 执行工具调用
            tool_messages = []
            for tool_call in response.tool_calls:
                tool_name = tool_call['name']
                tool_args = tool_call.get('args', {})
                
                # 查找并执行对应的工具
                for tool in self._tools:
                    if tool.name == tool_name:
                        try:
                            result = tool._run(
                                query=tool_args.get('query', ''),
                                context=tool_args.get('context', '')
                            )
                            tool_messages.append({
                                'role': 'tool',
                                'content': result,
                                'tool_call_id': tool_call.get('id', '')
                            })
                        except Exception as e:
                            tool_messages.append({
                                'role': 'tool',
                                'content': f"工具执行错误: {str(e)}",
                                'tool_call_id': tool_call.get('id', '')
                            })
                        break
            
            # 添加工具调用结果到消息，再次调用 LLM
            messages.append(response)
            for tm in tool_messages:
                from langchain_core.messages import ToolMessage
                messages.append(ToolMessage(
                    content=tm['content'],
                    tool_call_id=tm['tool_call_id']
                ))
            
            # 流式输出最终响应
            for chunk in self._llm.stream(messages):
                if chunk.content:
                    yield chunk.content
        else:
            # 没有工具调用，直接流式输出
            for chunk in self._llm.stream(messages):
                if chunk.content:
                    yield chunk.content
    
    def _convert_history(
        self,
        history: Optional[List[Dict[str, str]]] = None
    ) -> List[BaseMessage]:
        """
        转换历史消息格式
        
        Args:
            history: 历史消息列表 [{"role": "user", "content": "..."}]
            
        Returns:
            LangChain 消息列表
        """
        if not history:
            return []
        
        messages = []
        for msg in history:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
            elif role == "system":
                messages.append(SystemMessage(content=content))
        
        return messages
    
    def update_config(self, config: AgentConfig):
        """
        更新配置
        
        Args:
            config: 新的配置
        """
        self.config = config
        self._init_llm()
        self._rebuild_agent()
    
    def update_system_prompt(self, prompt: str):
        """
        更新系统提示词
        
        Args:
            prompt: 新的系统提示词
        """
        self.system_prompt = prompt
        self._rebuild_agent()
    
    def update_name(self, name: str):
        """
        更新名称
        
        Args:
            name: 新的名称
        """
        self.name = name
        self._rebuild_agent()


def create_agent(
    config: Dict[str, Any],
    name: str = "皮卡丘",
    system_prompt: str = ""
) -> PetAgent:
    """
    快捷函数：创建 Agent
    
    Args:
        config: 配置字典
        name: 宠物名称
        system_prompt: 系统提示词
        
    Returns:
        PetAgent 实例
    """
    agent_config = AgentConfig.from_dict(config)
    return PetAgent(agent_config, name, system_prompt)
