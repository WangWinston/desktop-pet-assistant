"""Skill Tool 模块 - 将 Skills 转换为 LangChain Tools"""
from typing import Any, Callable, Dict, List, Optional, Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool, tool
from langchain_core.callbacks import CallbackManagerForToolRun


class SkillInput(BaseModel):
    """技能工具输入模式"""
    query: str = Field(description="用户的问题或请求")
    context: Optional[str] = Field(default="", description="额外的上下文信息")


class SkillTool(BaseTool):
    """
    将 Skill 转换为 LangChain Tool
    
    每个 Skill 被包装成一个可调用的 Tool，
    Agent 可以根据用户输入决定是否调用该技能
    """
    
    name: str = ""
    description: str = ""
    args_schema: Type[BaseModel] = SkillInput
    skill_info: Dict[str, Any] = {}
    _handler: Optional[Callable] = None
    
    def __init__(
        self,
        name: str,
        description: str,
        skill_info: Dict[str, Any],
        handler: Optional[Callable] = None,
        **kwargs
    ):
        super().__init__(name=name, description=description, **kwargs)
        self.skill_info = skill_info
        self._handler = handler
    
    def _run(
        self,
        query: str,
        context: str = "",
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """
        执行技能
        
        Args:
            query: 用户的问题或请求
            context: 额外的上下文信息
            run_manager: 回调管理器
            
        Returns:
            技能执行结果
        """
        # 如果有自定义处理器，使用它
        if self._handler:
            return self._handler(query, context, self.skill_info)
        
        # 默认：返回技能的详细指导内容
        body = self.skill_info.get("body", "")
        skill_name = self.skill_info.get("name", self.name)
        
        if body:
            return f"【技能 {skill_name}】\n{body}"
        return f"技能 {skill_name} 已激活，但没有详细指导内容。"
    
    async def _arun(
        self,
        query: str,
        context: str = "",
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """异步执行（同步调用的别名）"""
        return self._run(query, context, run_manager)


class SkillToolChain:
    """
    链式技能工具加载器
    
    支持链式调用加载多个技能：
    
    ```python
    tools = (SkillToolChain()
        .load(skill_1)
        .load(skill_2)
        .load(skill_3)
        .build())
    ```
    """
    
    def __init__(self):
        self._tools: List[BaseTool] = []
        self._handlers: Dict[str, Callable] = {}
    
    def load(
        self,
        skill_info: Dict[str, Any],
        handler: Optional[Callable] = None
    ) -> "SkillToolChain":
        """
        加载单个技能
        
        Args:
            skill_info: 技能信息字典
            handler: 可选的自定义处理器
            
        Returns:
            返回自身，支持链式调用
        """
        name = skill_info.get("name") or skill_info.get("path", "").split("/")[-1]
        description = skill_info.get("description", f"技能: {name}")
        
        tool = SkillTool(
            name=name,
            description=description,
            skill_info=skill_info,
            handler=handler
        )
        self._tools.append(tool)
        
        if handler:
            self._handlers[name] = handler
        
        return self
    
    def load_batch(
        self,
        skills: Dict[str, Dict[str, Any]],
        handlers: Optional[Dict[str, Callable]] = None
    ) -> "SkillToolChain":
        """
        批量加载技能
        
        Args:
            skills: 技能字典 {skill_key: skill_info}
            handlers: 可选的处理器字典 {skill_name: handler}
            
        Returns:
            返回自身，支持链式调用
        """
        handlers = handlers or {}
        for skill_key, skill_info in skills.items():
            skill_name = skill_info.get("name", skill_key)
            handler = handlers.get(skill_name) or handlers.get(skill_key)
            self.load(skill_info, handler)
        return self
    
    def load_from_directory(
        self,
        directory: str,
        handlers: Optional[Dict[str, Callable]] = None
    ) -> "SkillToolChain":
        """
        从目录加载技能
        
        Args:
            directory: 技能目录路径
            handlers: 可选的处理器字典
            
        Returns:
            返回自身，支持链式调用
        """
        from core.persona import load_skills
        skills = load_skills(directory)
        return self.load_batch(skills, handlers)
    
    def with_handler(
        self,
        skill_name: str,
        handler: Callable
    ) -> "SkillToolChain":
        """
        为已加载的技能设置处理器
        
        Args:
            skill_name: 技能名称
            handler: 处理器函数
            
        Returns:
            返回自身，支持链式调用
        """
        self._handlers[skill_name] = handler
        # 更新对应 tool 的 handler
        for tool in self._tools:
            if tool.name == skill_name and isinstance(tool, SkillTool):
                tool._handler = handler
        return self
    
    def build(self) -> List[BaseTool]:
        """
        构建并返回工具列表
        
        Returns:
            LangChain Tool 列表
        """
        return self._tools.copy()
    
    def clear(self) -> "SkillToolChain":
        """
        清空已加载的工具
        
        Returns:
            返回自身，支持链式调用
        """
        self._tools.clear()
        self._handlers.clear()
        return self
    
    def __len__(self) -> int:
        """返回已加载的工具数量"""
        return len(self._tools)
    
    def __iter__(self):
        """支持迭代"""
        return iter(self._tools)


def create_skill_tools(
    skills: Dict[str, Dict[str, Any]],
    handlers: Optional[Dict[str, Callable]] = None
) -> List[BaseTool]:
    """
    快捷函数：从技能字典创建工具列表
    
    Args:
        skills: 技能字典
        handlers: 可选的处理器字典
        
    Returns:
        LangChain Tool 列表
    """
    return (SkillToolChain()
        .load_batch(skills, handlers)
        .build())


def skill_tool(
    name: str,
    description: str
) -> Callable:
    """
    装饰器：将函数转换为技能工具
    
    使用示例：
    ```python
    @skill_tool(name="weather", description="查询天气")
    def get_weather(query: str, context: str = "") -> str:
        return f"今天天气不错: {query}"
    ```
    
    Args:
        name: 工具名称
        description: 工具描述
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> BaseTool:
        @tool(name=name, description=description)
        def wrapper(query: str, context: str = "") -> str:
            return func(query, context)
        return wrapper
    return decorator
