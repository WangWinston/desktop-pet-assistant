"""上下文压缩器模块"""
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from core.chat import ChatService


class Compressor:
    """
    上下文压缩器
    当对话过长时，将历史对话压缩为摘要
    """

    # 压缩时保留的最近对话轮数
    KEEP_RECENT_TURNS = 5

    # 压缩提示词
    COMPRESS_PROMPT = """请将以下对话历史压缩为一段简短的摘要，保留重要信息（用户喜好、重要事件、约定等）：

{conversation}

摘要："""

    def __init__(self, chat_service: "ChatService"):
        """
        初始化压缩器

        Args:
            chat_service: 聊天服务实例
        """
        self.chat_service = chat_service

    def compress_messages(self, messages: List[dict]) -> List[dict]:
        """
        压缩消息列表

        保留：系统消息 + 摘要 + 最近N轮对话

        Args:
            messages: 原始消息列表

        Returns:
            压缩后的消息列表
        """
        # 消息太少不需要压缩
        min_messages = self.KEEP_RECENT_TURNS * 2 + 2  # 系统消息 + N轮对话
        if len(messages) <= min_messages:
            return messages

        # 分离系统消息和对话消息
        system_messages = [m for m in messages if m["role"] == "system"]
        conversation = [m for m in messages if m["role"] != "system"]

        # 保留最近 N 轮（每轮 2 条消息）
        keep_count = self.KEEP_RECENT_TURNS * 2
        if len(conversation) <= keep_count:
            return messages

        to_compress = conversation[:-keep_count]
        keep_recent = conversation[-keep_count:]

        # 生成摘要
        summary = self._generate_summary(to_compress)

        # 重组消息
        result = system_messages.copy()
        if summary:
            result.append(
                {
                    "role": "system",
                    "content": f"【历史对话摘要】\n{summary}",
                }
            )
        result.extend(keep_recent)

        return result

    def _generate_summary(self, messages: List[dict]) -> str:
        """
        生成对话摘要

        Args:
            messages: 需要压缩的消息列表

        Returns:
            摘要文本
        """
        # 格式化对话
        conversation_text = self._format_messages(messages)

        # 调用 AI 生成摘要
        prompt = self.COMPRESS_PROMPT.format(conversation=conversation_text)

        try:
            summary = self.chat_service.chat([{"role": "user", "content": prompt}])
            return summary.strip()
        except Exception as e:
            # 压缩失败时返回简单摘要
            return f"之前的对话共 {len(messages)} 条消息。（压缩失败：{str(e)}）"

    def _format_messages(self, messages: List[dict]) -> str:
        """
        格式化消息为文本

        Args:
            messages: 消息列表

        Returns:
            格式化后的文本
        """
        lines = []
        for m in messages:
            role = "用户" if m["role"] == "user" else "助手"
            content = m.get("content", "")
            # 截断过长的内容
            if len(content) > 200:
                content = content[:200] + "..."
            lines.append(f"{role}: {content}")
        return "\n".join(lines)

    def estimate_compressed_tokens(self, messages: List[dict]) -> int:
        """
        估算压缩后的 token 数

        Args:
            messages: 消息列表

        Returns:
            估算的 token 数
        """
        compressed = self.compress_messages(messages)
        return self.chat_service.count_tokens(compressed)