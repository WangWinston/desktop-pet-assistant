"""MCP 工具包装器 - 将 MCP 工具转换为 LangChain 工具"""
import asyncio
from typing import Any, Dict, Optional, Type
from pydantic import BaseModel, Field, create_model
from langchain_core.tools import BaseTool

from utils.logger import get_logger

log = get_logger("mcp_tools")


def create_schema_from_mcp(input_schema: dict, model_name: str = "MCPInput") -> Type[BaseModel]:
    """
    从 MCP inputSchema 创建 Pydantic 模型
    
    Args:
        input_schema: MCP 工具的 inputSchema
        model_name: 模型名称
        
    Returns:
        Pydantic 模型类
    """
    properties = input_schema.get("properties", {})
    required = input_schema.get("required", [])
    
    fields = {}
    for prop_name, prop_def in properties.items():
        prop_type = prop_def.get("type", "string")
        description = prop_def.get("description", "")
        
        # 类型映射
        python_type = str
        if prop_type == "integer":
            python_type = int
        elif prop_type == "number":
            python_type = float
        elif prop_type == "boolean":
            python_type = bool
        elif prop_type == "array":
            python_type = list
        elif prop_type == "object":
            python_type = dict
        
        # 是否必填
        if prop_name in required:
            fields[prop_name] = (python_type, Field(description=description))
        else:
            fields[prop_name] = (Optional[python_type], Field(default=None, description=description))
    
    # 确保至少有一个字段
    if not fields:
        fields["_placeholder"] = (str, Field(default="", description="Placeholder field"))
    
    return create_model(model_name, **fields)


class MCPToolWrapper(BaseTool):
    """MCP 工具包装器 - 将 MCP 工具包装为 LangChain Tool"""
    
    name: str = ""
    description: str = ""
    server_name: str = ""
    tool_name: str = ""
    args_schema: Type[BaseModel] = None
    
    def __init__(
        self,
        name: str,
        description: str,
        server_name: str,
        tool_name: str,
        input_schema: dict,
        **kwargs
    ):
        # 创建参数模型
        args_schema = create_schema_from_mcp(input_schema, f"{name}Input")
        
        super().__init__(
            name=name,
            description=description,
            server_name=server_name,
            tool_name=tool_name,
            args_schema=args_schema,
            **kwargs
        )
    
    def _run(self, **kwargs) -> str:
        """同步执行（内部调用异步）"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果已经在异步环境中，创建新线程执行
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self._arun(**kwargs))
                    return future.result()
            else:
                return loop.run_until_complete(self._arun(**kwargs))
        except Exception as e:
            log.error(f"MCP 工具执行失败: {e}")
            return f"工具执行失败: {str(e)}"
    
    async def _arun(self, **kwargs) -> str:
        """异步执行"""
        from core.mcp_client import get_mcp_manager
        
        manager = get_mcp_manager()
        
        try:
            result = await manager.call_tool(
                self.server_name,
                self.tool_name,
                kwargs
            )
            
            # 处理结果
            if hasattr(result, 'content'):
                # MCP 返回结果对象
                content = result.content
                if isinstance(content, list):
                    # 合并多个内容块
                    texts = []
                    for item in content:
                        if hasattr(item, 'text'):
                            texts.append(item.text)
                        elif isinstance(item, str):
                            texts.append(item)
                    return "\n".join(texts)
                return str(content)
            
            return str(result)
            
        except Exception as e:
            log.error(f"调用 MCP 工具失败 {self.name}: {e}")
            return f"工具调用失败: {str(e)}"


def create_mcp_langchain_tool(mcp_tool) -> BaseTool:
    """
    从 MCPTool 创建 LangChain 工具
    
    Args:
        mcp_tool: MCPTool 实例
        
    Returns:
        LangChain BaseTool 实例
    """
    return MCPToolWrapper(
        name=f"mcp_{mcp_tool.server_name}_{mcp_tool.name}",
        description=f"[MCP:{mcp_tool.server_name}] {mcp_tool.description}",
        server_name=mcp_tool.server_name,
        tool_name=mcp_tool.name,
        input_schema=mcp_tool.input_schema,
    )


class MCPToolChain:
    """
    MCP 工具链 - 链式加载 MCP 工具
    
    使用示例:
    ```python
    tools = (MCPToolChain()
        .from_server("filesystem", fs_connection)
        .from_server("brave-search", search_connection)
        .build())
    ```
    """
    
    def __init__(self):
        self._tools: list = []
    
    def from_server(self, server_name: str, connection) -> "MCPToolChain":
        """从服务器连接加载工具"""
        for mcp_tool in connection.tools:
            try:
                lc_tool = create_mcp_langchain_tool(mcp_tool)
                self._tools.append(lc_tool)
            except Exception as e:
                log.warning(f"加载 MCP 工具失败 {mcp_tool.name}: {e}")
        return self
    
    def from_manager(self, manager) -> "MCPToolChain":
        """从 MCP 管理器加载所有工具"""
        self._tools.extend(manager.get_langchain_tools())
        return self
    
    def build(self) -> list:
        """构建并返回工具列表"""
        return self._tools.copy()
    
    def __len__(self) -> int:
        return len(self._tools)
