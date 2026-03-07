"""MCP (Model Context Protocol) 配置模块"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
import json


@dataclass
class MCPServerConfig:
    """MCP 服务器配置"""
    name: str
    transport: str  # "stdio" 或 "sse"
    command: Optional[str] = None  # stdio 传输时的命令
    args: List[str] = field(default_factory=list)  # 命令参数
    url: Optional[str] = None  # SSE 传输时的 URL
    env: Dict[str, str] = field(default_factory=dict)  # 环境变量
    enabled: bool = True
    description: str = ""
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "transport": self.transport,
            "command": self.command,
            "args": self.args,
            "url": self.url,
            "env": self.env,
            "enabled": self.enabled,
            "description": self.description,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "MCPServerConfig":
        return cls(
            name=data.get("name", "unknown"),
            transport=data.get("transport", "stdio"),
            command=data.get("command"),
            args=data.get("args", []),
            url=data.get("url"),
            env=data.get("env", {}),
            enabled=data.get("enabled", True),
            description=data.get("description", ""),
        )


@dataclass
class MCPConfig:
    """MCP 总配置"""
    enabled: bool = True
    servers: List[MCPServerConfig] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "servers": [s.to_dict() for s in self.servers],
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "MCPConfig":
        servers = []
        for server_data in data.get("servers", []):
            servers.append(MCPServerConfig.from_dict(server_data))
        return cls(
            enabled=data.get("enabled", True),
            servers=servers,
        )
    
    def get_enabled_servers(self) -> List[MCPServerConfig]:
        """获取所有启用的服务器"""
        return [s for s in self.servers if s.enabled]


# 预定义的常用 MCP 服务器配置
PREDEFINED_MCP_SERVERS = {
    "filesystem": MCPServerConfig(
        name="filesystem",
        transport="stdio",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "."],
        description="文件系统访问，允许读写文件",
    ),
    "brave-search": MCPServerConfig(
        name="brave-search",
        transport="stdio",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-brave-search"],
        env={"BRAVE_API_KEY": ""},
        description="Brave 搜索，网络搜索能力",
    ),
    "memory": MCPServerConfig(
        name="memory",
        transport="stdio",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-memory"],
        description="记忆存储，持久化对话记忆",
    ),
    "github": MCPServerConfig(
        name="github",
        transport="stdio",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-github"],
        env={"GITHUB_TOKEN": ""},
        description="GitHub 集成，仓库操作",
    ),
    "postgres": MCPServerConfig(
        name="postgres",
        transport="stdio",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-postgres"],
        env={"POSTGRES_CONNECTION_STRING": ""},
        description="PostgreSQL 数据库访问",
    ),
    "fetch": MCPServerConfig(
        name="fetch",
        transport="stdio",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-fetch"],
        description="HTTP 请求，获取网页内容",
    ),
}


def load_mcp_config(config_path: str = "mcp_config.json") -> MCPConfig:
    """
    从文件加载 MCP 配置
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        MCPConfig 实例
    """
    path = Path(config_path)
    if not path.exists():
        return MCPConfig()
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return MCPConfig.from_dict(data)
    except Exception as e:
        print(f"加载 MCP 配置失败: {e}")
        return MCPConfig()


def save_mcp_config(config: MCPConfig, config_path: str = "mcp_config.json"):
    """
    保存 MCP 配置到文件
    
    Args:
        config: MCPConfig 实例
        config_path: 配置文件路径
    """
    path = Path(config_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)


def create_default_mcp_config() -> MCPConfig:
    """创建默认 MCP 配置（包含预定义服务器但禁用）"""
    servers = []
    for name, server in PREDEFINED_MCP_SERVERS.items():
        # 默认禁用，需要用户配置后启用
        server.enabled = False
        servers.append(server)
    
    return MCPConfig(enabled=False, servers=servers)
