"""上下文管理模块"""
import json
import os
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional, Tuple

if TYPE_CHECKING:
    from core.chat import ChatService
    from core.compressor import Compressor


class MemoryManager:
    """
    上下文管理器
    负责对话历史的存储、加载和压缩
    """

    def __init__(self, config: dict, chat_service: "ChatService", compressor: "Compressor"):
        """
        初始化上下文管理器

        Args:
            config: 配置字典
            chat_service: 聊天服务实例
            compressor: 压缩器实例
        """
        self.config = config
        self.chat_service = chat_service
        self.compressor = compressor

        # 消息列表
        self.messages: List[dict] = []

        # 统计信息
        self.stats = {
            "total_messages": 0,
            "compressions_done": 0,
        }

        # 配置
        history_config = config.get("history", {})
        self.history_file = history_config.get("file", "data/chat_history.json")
        self.auto_save = history_config.get("auto_save", True)

        chat_config = config.get("chat", {})
        self.context_limit = chat_config.get("context_limit", 128000)
        self.compress_threshold = chat_config.get("compress_threshold", 0.8)

        # 时间戳
        self.created_at: Optional[str] = None

    def add_message(self, role: str, content: str):
        """
        添加消息到历史

        Args:
            role: 角色 (user/assistant/system)
            content: 消息内容
        """
        self.messages.append({"role": role, "content": content})
        self.stats["total_messages"] += 1

        if self.auto_save:
            self.save_to_file()

    def get_messages(self) -> List[dict]:
        """
        获取消息列表的副本

        Returns:
            消息列表
        """
        return self.messages.copy()

    def get_token_count(self) -> int:
        """
        获取当前 token 数

        Returns:
            token 数量
        """
        return self.chat_service.count_tokens(self.messages)

    def get_context_usage(self) -> Tuple[int, int, float]:
        """
        获取上下文使用情况

        Returns:
            (当前token, 上限, 使用比例)
        """
        current = self.get_token_count()
        limit = self.context_limit
        ratio = current / limit if limit > 0 else 0
        return current, limit, ratio

    def should_compress(self) -> bool:
        """
        判断是否需要压缩

        Returns:
            是否需要压缩
        """
        current, limit, ratio = self.get_context_usage()
        return ratio >= self.compress_threshold

    def compress(self) -> str:
        """
        执行压缩

        Returns:
            提示信息
        """
        self.messages = self.compressor.compress_messages(self.messages)
        self.stats["compressions_done"] += 1

        if self.auto_save:
            self.save_to_file()

        return "✓ 记忆整理完成"

    def save_to_file(self):
        """保存到文件"""
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)

        data = {
            "version": 1,
            "created_at": self.created_at or datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "messages": self.messages,
            "stats": self.stats,
        }

        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_from_file(self) -> bool:
        """
        从文件加载

        Returns:
            是否成功加载
        """
        if not os.path.exists(self.history_file):
            return False

        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.messages = data.get("messages", [])
            self.stats = data.get("stats", {"total_messages": 0, "compressions_done": 0})
            self.created_at = data.get("created_at")
            return True
        except (json.JSONDecodeError, IOError):
            return False

    def clear(self):
        """清空历史"""
        self.messages = []
        self.stats = {"total_messages": 0, "compressions_done": 0}
        self.save_to_file()