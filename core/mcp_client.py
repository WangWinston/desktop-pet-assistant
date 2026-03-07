"""MCP 客户端管理器"""
import asyncio
import os
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from utils.logger import get_logger

log = get_logger("mcp")

# MCP SDK imports
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
    log.debug("MCP SDK 加载成功")
except ImportError as e:
    MCP_AVAILABLE = False
    log.warning(f"MCP SDK 未安装，MCP 功能不可用: {e}")


class MCPTool:
    """MCP 工具包装"""
    
    def __init__(self, name: str, description: str, server_name: str, input_schema: dict):
        self.name = name
        self.description = description
        self.server_name = server_name
        self.input_schema = input_schema
    
    def to_langchain_tool(self) -> "BaseTool":
        """转换为 LangChain Tool"""
        from core.mcp_tools import create_mcp_langchain_tool
        return create_mcp_langchain_tool(self)


class MCPServerConnection:
    """MCP 服务器连接"""
    
    def __init__(self, server_config, session=None):
        self.config = server_config
        self.session = session
        self.tools: List[MCPTool] = []
        self.resources: List[dict] = []
        self._connected = False
    
    @property
    def is_connected(self) -> bool:
        return self._connected and self.session is not None
    
    async def connect(self) -> bool:
        """连接到 MCP 服务器"""
        if not MCP_AVAILABLE:
            log.warning(f"MCP SDK 不可用，无法连接服务器: {self.config.name}")
            return False
        
        try:
            if self.config.transport == "stdio":
                return await self._connect_stdio()
            elif self.config.transport == "sse":
                return await self._connect_sse()
            else:
                log.error(f"不支持的传输类型: {self.config.transport}")
                return False
        except Exception as e:
            log.error(f"连接 MCP 服务器失败 {self.config.name}: {e}")
            return False
    
    async def _connect_stdio(self) -> bool:
        """通过 stdio 连接"""
        if not self.config.command:
            log.error(f"stdio 传输需要指定 command")
            return False
        
        # 准备环境变量
        env = os.environ.copy()
        env.update(self.config.env)
        
        server_params = StdioServerParameters(
            command=self.config.command,
            args=self.config.args,
            env=env,
        )
        
        try:
            self._stdio_context = stdio_client(server_params)
            read, write = await self._stdio_context.__aenter__()
            
            self.session = ClientSession(read, write)
            await self.session.__aenter__()
            
            # 初始化会话
            await self.session.initialize()
            
            # 获取工具列表
            await self._load_tools()
            
            self._connected = True
            log.info(f"已连接 MCP 服务器: {self.config.name}, 工具数: {len(self.tools)}")
            return True
            
        except Exception as e:
            log.error(f"stdio 连接失败: {e}")
            return False
    
    async def _connect_sse(self) -> bool:
        """通过 SSE 连接"""
        # SSE 连接需要额外的实现
        log.warning(f"SSE 传输暂不支持: {self.config.name}")
        return False
    
    async def _load_tools(self):
        """加载服务器提供的工具"""
        if not self.session:
            return
        
        try:
            tools_result = await self.session.list_tools()
            for tool in tools_result.tools:
                mcp_tool = MCPTool(
                    name=tool.name,
                    description=tool.description or "",
                    server_name=self.config.name,
                    input_schema=tool.inputSchema or {},
                )
                self.tools.append(mcp_tool)
                log.debug(f"加载 MCP 工具: {tool.name}")
        except Exception as e:
            log.error(f"加载工具列表失败: {e}")
    
    async def call_tool(self, tool_name: str, arguments: dict) -> Any:
        """调用工具"""
        if not self.session:
            raise RuntimeError(f"服务器未连接: {self.config.name}")
        
        try:
            result = await self.session.call_tool(tool_name, arguments)
            return result
        except Exception as e:
            log.error(f"调用 MCP 工具失败 {tool_name}: {e}")
            raise
    
    async def disconnect(self):
        """断开连接"""
        try:
            if self.session:
                await self.session.__aexit__(None, None, None)
            if hasattr(self, '_stdio_context'):
                await self._stdio_context.__aexit__(None, None, None)
        except Exception as e:
            log.warning(f"断开连接时出错: {e}")
        finally:
            self.session = None
            self._connected = False


class MCPManager:
    """MCP 管理器 - 管理所有 MCP 服务器连接"""
    
    def __init__(self):
        self.connections: Dict[str, MCPServerConnection] = {}
        self._tools_cache: Optional[List[MCPTool]] = None
    
    async def connect_server(self, server_config) -> bool:
        """连接单个服务器"""
        if server_config.name in self.connections:
            log.warning(f"服务器已连接: {server_config.name}")
            return True
        
        connection = MCPServerConnection(server_config)
        success = await connection.connect()
        
        if success:
            self.connections[server_config.name] = connection
            self._tools_cache = None  # 清除缓存
        
        return success
    
    async def connect_all(self, servers: list) -> Dict[str, bool]:
        """连接所有服务器"""
        results = {}
        for server in servers:
            results[server.name] = await self.connect_server(server)
        return results
    
    async def disconnect_server(self, server_name: str):
        """断开单个服务器"""
        if server_name in self.connections:
            await self.connections[server_name].disconnect()
            del self.connections[server_name]
            self._tools_cache = None
    
    async def disconnect_all(self):
        """断开所有服务器"""
        for name in list(self.connections.keys()):
            await self.disconnect_server(name)
    
    def get_all_tools(self) -> List[MCPTool]:
        """获取所有工具"""
        if self._tools_cache is not None:
            return self._tools_cache
        
        tools = []
        for connection in self.connections.values():
            tools.extend(connection.tools)
        
        self._tools_cache = tools
        return tools
    
    def get_langchain_tools(self) -> List["BaseTool"]:
        """获取所有工具（LangChain 格式）"""
        tools = []
        for mcp_tool in self.get_all_tools():
            try:
                lc_tool = mcp_tool.to_langchain_tool()
                tools.append(lc_tool)
            except Exception as e:
                log.warning(f"转换工具失败 {mcp_tool.name}: {e}")
        return tools
    
    async def call_tool(self, server_name: str, tool_name: str, arguments: dict) -> Any:
        """调用指定服务器的工具"""
        if server_name not in self.connections:
            raise ValueError(f"服务器未连接: {server_name}")
        
        return await self.connections[server_name].call_tool(tool_name, arguments)
    
    def find_tool_server(self, tool_name: str) -> Optional[str]:
        """查找工具所属的服务器"""
        for server_name, connection in self.connections.items():
            for tool in connection.tools:
                if tool.name == tool_name:
                    return server_name
        return None
    
    @property
    def is_available(self) -> bool:
        """MCP 是否可用"""
        return MCP_AVAILABLE


# 全局单例
_mcp_manager: Optional[MCPManager] = None


def get_mcp_manager() -> MCPManager:
    """获取 MCP 管理器单例"""
    global _mcp_manager
    if _mcp_manager is None:
        _mcp_manager = MCPManager()
    return _mcp_manager


async def initialize_mcp(config) -> MCPManager:
    """
    初始化 MCP 系统
    
    Args:
        config: MCPConfig 实例
        
    Returns:
        MCPManager 实例
    """
    manager = get_mcp_manager()
    
    if not config.enabled:
        log.info("MCP 功能已禁用")
        return manager
    
    if not MCP_AVAILABLE:
        log.warning("MCP SDK 未安装，跳过初始化")
        return manager
    
    enabled_servers = config.get_enabled_servers()
    if not enabled_servers:
        log.info("没有启用的 MCP 服务器")
        return manager
    
    log.info(f"开始连接 {len(enabled_servers)} 个 MCP 服务器...")
    
    results = await manager.connect_all(enabled_servers)
    
    success_count = sum(1 for v in results.values() if v)
    log.info(f"MCP 初始化完成: {success_count}/{len(results)} 个服务器连接成功")
    
    return manager
