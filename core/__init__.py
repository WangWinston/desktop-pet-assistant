"""Core 模块 - 核心 AI 功能"""

from core.chat import ChatService, ChatError, create_chat_service
from core.memory import MemoryManager
from core.compressor import Compressor
from core.persona import (
    PersonaManager,
    SkillLoader,
    load_skills,
    build_skills_prompt,
    build_system_prompt,
    USER_PROFILE_DIMENSIONS,
    DIMENSION_DESCRIPTIONS,
    DEFAULT_NAME,
    DEFAULT_DUTIES,
)
from core.skill_tool import (
    SkillTool,
    SkillToolChain,
    create_skill_tools,
    skill_tool,
)
from core.agent import (
    PetAgent,
    AgentConfig,
    create_agent,
)
from core.agent_chat import (
    AgentChatService,
    AgentChatFactory,
    create_agent_chat_service,
)
from core.mcp_config import (
    MCPConfig,
    MCPServerConfig,
    PREDEFINED_MCP_SERVERS,
    load_mcp_config,
    save_mcp_config,
)
from core.mcp_client import (
    MCPManager,
    MCPServerConnection,
    MCPTool,
    get_mcp_manager,
    initialize_mcp,
)
from core.mcp_tools import (
    MCPToolWrapper,
    MCPToolChain,
    create_mcp_langchain_tool,
)

__all__ = [
    # 传统 Chat 服务
    "ChatService",
    "ChatError",
    "create_chat_service",
    # 记忆管理
    "MemoryManager",
    # 压缩器
    "Compressor",
    # 人设管理
    "PersonaManager",
    "SkillLoader",
    "load_skills",
    "build_skills_prompt",
    "build_system_prompt",
    "USER_PROFILE_DIMENSIONS",
    "DIMENSION_DESCRIPTIONS",
    "DEFAULT_NAME",
    "DEFAULT_DUTIES",
    # 技能工具
    "SkillTool",
    "SkillToolChain",
    "create_skill_tools",
    "skill_tool",
    # Agent
    "PetAgent",
    "AgentConfig",
    "create_agent",
    # Agent Chat 适配器
    "AgentChatService",
    "AgentChatFactory",
    "create_agent_chat_service",
    # MCP 配置
    "MCPConfig",
    "MCPServerConfig",
    "PREDEFINED_MCP_SERVERS",
    "load_mcp_config",
    "save_mcp_config",
    # MCP 客户端
    "MCPManager",
    "MCPServerConnection",
    "MCPTool",
    "get_mcp_manager",
    "initialize_mcp",
    # MCP 工具
    "MCPToolWrapper",
    "MCPToolChain",
    "create_mcp_langchain_tool",
]