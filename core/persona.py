"""人设管理模块"""
from typing import List, Optional


class PersonaManager:
    """人设管理器，负责管理 AI 人设和用户偏好"""

    def __init__(self, config: dict):
        self.config = config
        persona_config = config.get("persona", {})
        self.name = persona_config.get("name", "助手")
        self.system_prompt = persona_config.get("system_prompt", "你是一个有用的助手。")
        self.user_preferences: List[str] = persona_config.get("user_preferences", [])

    def get_system_message(self) -> dict:
        """
        获取完整的系统消息

        Returns:
            系统消息字典 {"role": "system", "content": "..."}
        """
        content = self.system_prompt
        if self.user_preferences:
            prefs = "\n".join(f"- {p}" for p in self.user_preferences)
            content += f"\n\n关于用户：\n{prefs}"
        return {"role": "system", "content": content}

    def update_system_prompt(self, new_prompt: str):
        """
        更新系统提示

        Args:
            new_prompt: 新的系统提示
        """
        self.system_prompt = new_prompt
        if "persona" not in self.config:
            self.config["persona"] = {}
        self.config["persona"]["system_prompt"] = new_prompt

    def add_preference(self, preference: str):
        """
        添加用户偏好

        Args:
            preference: 用户偏好描述
        """
        if preference not in self.user_preferences:
            self.user_preferences.append(preference)
            if "persona" not in self.config:
                self.config["persona"] = {}
            self.config["persona"]["user_preferences"] = self.user_preferences

    def remove_preference(self, index: int) -> bool:
        """
        移除用户偏好

        Args:
            index: 偏好索引

        Returns:
            是否成功移除
        """
        if 0 <= index < len(self.user_preferences):
            self.user_preferences.pop(index)
            self.config["persona"]["user_preferences"] = self.user_preferences
            return True
        return False

    def set_preferences(self, preferences: List[str]):
        """
        设置用户偏好列表

        Args:
            preferences: 新的用户偏好列表
        """
        self.user_preferences = preferences
        if "persona" not in self.config:
            self.config["persona"] = {}
        self.config["persona"]["user_preferences"] = preferences

    def set_name(self, name: str):
        """
        设置人设名称

        Args:
            name: 新名称
        """
        self.name = name
        if "persona" not in self.config:
            self.config["persona"] = {}
        self.config["persona"]["name"] = name

    def reset_to_default(self):
        """重置为默认人设"""
        self.name = "皮卡丘"
        self.system_prompt = "你是一只可爱的桌面宠物皮卡丘。"
        self.user_preferences = []
        self.config["persona"] = {
            "name": self.name,
            "system_prompt": self.system_prompt,
            "user_preferences": self.user_preferences,
        }

    def to_dict(self) -> dict:
        """导出为字典"""
        return {
            "name": self.name,
            "system_prompt": self.system_prompt,
            "user_preferences": self.user_preferences.copy(),
        }