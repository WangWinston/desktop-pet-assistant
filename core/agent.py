"""LangChain Agent 模块 - 基于技能的智能代理"""
from typing import Any, Callable, Dict, List, Optional, Sequence, Generator, Union
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_core.tools import BaseTool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.callbacks import BaseCallbackHandler

from core.skill_tool import SkillToolChain, create_skill_tools
from utils.logger import get_logger

# 模块日志
log = get_logger("agent")


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
回复时请保持友好、活泼的语气。

## 输出格式要求
请使用 Markdown 格式输出回复，包括：
- 使用 **粗体** 强调重要内容
- 使用 `代码` 或 ```代码块``` 展示代码
- 使用 - 或 1. 2. 3. 展示列表
- 使用 ## ### 标题组织内容
- 使用 > 引用重要信息"""
    
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
        log.info(f"初始化 LLM: model={self.config.model}, base_url={self.config.base_url}")
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
            log.debug(f"绑定 {len(self._tools)} 个工具到 LLM")
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
        skill_name = skill_info.get("name", "unknown")
        log.info(f"加载技能: {skill_name}")
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
        log.info(f"批量加载 {len(skills)} 个技能: {list(skills.keys())}")
        self.tool_chain.load_batch(skills, handlers)
        self._tools = self.tool_chain.build()
        self._rebuild_agent()
        return self
    
    def load_mcp_tools(self, mcp_manager=None) -> "PetAgent":
        """
        从 MCP 管理器加载工具
        
        Args:
            mcp_manager: MCP 管理器实例，如果为 None 则获取全局实例
            
        Returns:
            返回自身，支持链式调用
        """
        try:
            from core.mcp_client import get_mcp_manager
            from core.mcp_tools import MCPToolChain
            
            manager = mcp_manager or get_mcp_manager()
            
            if not manager.is_available:
                log.debug("MCP 不可用，跳过加载 MCP 工具")
                return self
            
            mcp_tools = MCPToolChain().from_manager(manager).build()
            
            if mcp_tools:
                log.info(f"加载 {len(mcp_tools)} 个 MCP 工具")
                self._tools.extend(mcp_tools)
                self._rebuild_agent()
            else:
                log.debug("没有可用的 MCP 工具")
                
        except ImportError as e:
            log.warning(f"MCP SDK 未安装: {e}")
        except Exception as e:
            log.error(f"加载 MCP 工具失败: {e}")
        
        return self
    
    def load_builtin_tools(self) -> "PetAgent":
        """
        加载内置工具（文件系统操作 + 命令执行）
        
        Returns:
            返回自身，支持链式调用
        """
        from langchain_core.tools import Tool
        
        def read_file_func(file_path: str) -> str:
            """读取文件内容"""
            import os
            abs_path = os.path.abspath(file_path)
            if not os.path.exists(abs_path):
                return f"文件不存在: {file_path}"
            try:
                with open(abs_path, "r", encoding="utf-8") as f:
                    content = f.read()
                return f"文件: {file_path}\n内容:\n{content}"
            except Exception as e:
                return f"读取文件失败: {str(e)}"
        
        def write_file_func(file_path: str, content: str) -> str:
            """写入文件内容"""
            import os
            abs_path = os.path.abspath(file_path)
            try:
                # 确保目录存在
                os.makedirs(os.path.dirname(abs_path), exist_ok=True)
                with open(abs_path, "w", encoding="utf-8") as f:
                    f.write(content)
                return f"文件已写入: {file_path}"
            except Exception as e:
                return f"写入文件失败: {str(e)}"
        
        def execute_command_func(command: str) -> str:
            """执行命令行指令"""
            import subprocess
            import os
            
            # 安全检查：禁止危险命令
            dangerous_patterns = ["rm -rf /", "format", "del /f /s /q", "shutdown", "restart"]
            for pattern in dangerous_patterns:
                if pattern.lower() in command.lower():
                    return f"拒绝执行危险命令: {command}"
            
            try:
                # 在项目目录下执行
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    encoding="utf-8",
                    errors="ignore",
                    cwd=os.getcwd()
                )
                output = result.stdout
                if result.stderr:
                    output += f"\n错误:\n{result.stderr}"
                if not output:
                    output = "命令执行成功，无输出"
                return output
            except subprocess.TimeoutExpired:
                return "命令执行超时（30秒）"
            except Exception as e:
                return f"命令执行失败: {str(e)}"
        
        # 创建内置工具
        read_tool = Tool(
            name="read_file",
            description="读取文件内容。输入文件路径，返回文件内容。用于查看代码、配置文件等。",
            func=read_file_func
        )
        
        write_tool = Tool(
            name="write_file",
            description="写入文件内容。输入文件路径和内容，将内容写入文件。用于创建或修改代码、配置文件等。",
            func=write_file_func
        )
        
        exec_tool = Tool(
            name="execute_command",
            description="执行命令行指令。输入要执行的命令，返回命令输出。用于运行Python脚本、安装依赖、执行git命令等。注意：危险命令会被拒绝执行。",
            func=execute_command_func
        )
        
        # 检查是否已存在
        existing_names = {t.name for t in self._tools}
        if "read_file" not in existing_names:
            self._tools.append(read_tool)
            log.info("添加内置工具: read_file")
        if "write_file" not in existing_names:
            self._tools.append(write_tool)
            log.info("添加内置工具: write_file")
        if "execute_command" not in existing_names:
            self._tools.append(exec_tool)
            log.info("添加内置工具: execute_command")
        
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
        log.info(f"从目录加载技能: {directory}")
        self.tool_chain.load_from_directory(directory, handlers)
        self._tools = self.tool_chain.build()
        log.debug(f"已加载 {len(self._tools)} 个工具")
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
        log.debug(f"chat() 收到消息: {message[:100]}...")
        
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
        log.debug(f"使用 LLM: {'with_tools' if self._llm_with_tools else 'plain'}")
        
        try:
            response = llm_to_use.invoke(messages)
        except Exception as e:
            log.error(f"LLM 调用失败: {e}")
            return f"抱歉，处理消息时出错了: {str(e)}"
        
        # 如果有工具调用，执行工具并获取最终响应
        if hasattr(response, 'tool_calls') and response.tool_calls:
            log.info(f"检测到 {len(response.tool_calls)} 个工具调用")
            # 执行工具调用
            tool_messages = []
            for tool_call in response.tool_calls:
                tool_name = tool_call['name']
                tool_args = tool_call.get('args', {})
                log.info(f"执行工具: {tool_name}, 参数: {tool_args}")
                
                # 查找并执行对应的工具
                tool_found = False
                for tool in self._tools:
                    if tool.name == tool_name:
                        tool_found = True
                        try:
                            result = tool._run(
                                query=tool_args.get('query', ''),
                                context=tool_args.get('context', '')
                            )
                            log.debug(f"工具 {tool_name} 执行成功, 结果长度: {len(result)}")
                            tool_messages.append({
                                'role': 'tool',
                                'content': result,
                                'tool_call_id': tool_call.get('id', '')
                            })
                        except Exception as e:
                            log.error(f"工具 {tool_name} 执行失败: {e}")
                            tool_messages.append({
                                'role': 'tool',
                                'content': f"工具执行错误: {str(e)}",
                                'tool_call_id': tool_call.get('id', '')
                            })
                        break
                
                if not tool_found:
                    log.warning(f"未找到工具: {tool_name}")
            
            # 添加工具调用结果到消息，再次调用 LLM
            messages.append(response)
            for tm in tool_messages:
                from langchain_core.messages import ToolMessage
                messages.append(ToolMessage(
                    content=tm['content'],
                    tool_call_id=tm['tool_call_id']
                ))
            
            log.debug("调用 LLM 生成最终响应...")
            try:
                final_response = self._llm.invoke(messages)
                return final_response.content
            except Exception as e:
                log.error(f"最终响应生成失败: {e}")
                return f"工具调用后生成响应失败: {str(e)}"
        
        log.debug(f"无工具调用，直接返回响应")
        # 清理 MiniMax 模型的工具调用标记
        content = response.content
        content = self._clean_tool_call_markers(content)
        return content
    
    def _clean_tool_call_markers(self, content: str) -> str:
        """清理 MiniMax 模型的工具调用标记"""
        import re
        # 移除 minimax:tool_call ... /minimax:tool_call 标记及其内容
        content = re.sub(r'minimax:tool_call\s*.*?/minimax:tool_call', '', content, flags=re.DOTALL)
        # 移除可能残留的单独标记
        content = re.sub(r'minimax:tool_call\s*', '', content)
        content = re.sub(r'/minimax:tool_call\s*', '', content)
        # 移除其他常见工具调用标记
        content = re.sub(r'<antml:function_calls>.*?</antml:function_calls>', '', content, flags=re.DOTALL)
        content = re.sub(r'<function_calls>.*?</function_calls>', '', content, flags=re.DOTALL)
        # 清理多余空白
        content = re.sub(r'\n{3,}', '\n\n', content)
        return content.strip()
    
    def _should_filter_chunk(self, content: str) -> bool:
        """判断是否应该过滤掉这个 chunk（包含工具调用标记）"""
        markers = ['minimax:tool_call', '/minimax:tool_call', '', '<function_calls>']
        for marker in markers:
            if marker in content:
                return True
        return False
    
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
        log.debug(f"chat_stream() 收到消息: {message[:100]}...")
        
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
        log.debug(f"使用 LLM: {'with_tools' if self._llm_with_tools else 'plain'}")
        
        try:
            # 先检查是否有工具调用
            response = llm_to_use.invoke(messages)
        except Exception as e:
            log.error(f"LLM 调用失败: {e}")
            yield f"抱歉，处理消息时出错了: {str(e)}"
            return
        
        # 如果有工具调用，执行工具并获取最终响应
        if hasattr(response, 'tool_calls') and response.tool_calls:
            log.info(f"检测到 {len(response.tool_calls)} 个工具调用")
            # 执行工具调用
            tool_messages = []
            for tool_call in response.tool_calls:
                tool_name = tool_call['name']
                tool_args = tool_call.get('args', {})
                log.info(f"执行工具: {tool_name}, 参数: {tool_args}")
                
                # 查找并执行对应的工具
                tool_found = False
                for tool in self._tools:
                    if tool.name == tool_name:
                        tool_found = True
                        try:
                            result = tool._run(
                                query=tool_args.get('query', ''),
                                context=tool_args.get('context', '')
                            )
                            log.debug(f"工具 {tool_name} 执行成功, 结果长度: {len(result)}")
                            tool_messages.append({
                                'role': 'tool',
                                'content': result,
                                'tool_call_id': tool_call.get('id', '')
                            })
                        except Exception as e:
                            log.error(f"工具 {tool_name} 执行失败: {e}")
                            tool_messages.append({
                                'role': 'tool',
                                'content': f"工具执行错误: {str(e)}",
                                'tool_call_id': tool_call.get('id', '')
                            })
                        break
                
                if not tool_found:
                    log.warning(f"未找到工具: {tool_name}")
            
            # 添加工具调用结果到消息，再次调用 LLM
            messages.append(response)
            for tm in tool_messages:
                from langchain_core.messages import ToolMessage
                messages.append(ToolMessage(
                    content=tm['content'],
                    tool_call_id=tm['tool_call_id']
                ))
            
            log.debug("流式输出最终响应...")
            chunk_count = 0
            try:
                # 流式输出最终响应
                for chunk in self._llm.stream(messages):
                    if chunk.content:
                        chunk_count += 1
                        if chunk_count <= 3:  # 只记录前几个 chunk
                            log.debug(f"chunk {chunk_count}: {chunk.content[:50]}...")
                        # 清理 MiniMax 工具调用标记
                        cleaned = self._clean_tool_call_markers(chunk.content)
                        if cleaned:
                            yield cleaned
                log.debug(f"流式输出完成, chunks={chunk_count}")
            except Exception as e:
                log.error(f"流式输出失败: {e}")
                yield f"生成响应失败: {str(e)}"
        else:
            log.debug("无工具调用，直接流式输出")
            chunk_count = 0
            try:
                # 没有工具调用，直接流式输出
                for chunk in self._llm.stream(messages):
                    if chunk.content:
                        chunk_count += 1
                        # 清理 MiniMax 工具调用标记
                        cleaned = self._clean_tool_call_markers(chunk.content)
                        if cleaned:
                            yield cleaned
                log.debug(f"流式输出完成, chunks={chunk_count}")
            except Exception as e:
                log.error(f"流式输出失败: {e}")
                yield f"生成响应失败: {str(e)}"
    
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
