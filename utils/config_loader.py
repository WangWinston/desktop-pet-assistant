"""配置加载器模块"""
import os
import shutil

import yaml


class ConfigLoader:
    """配置加载器，负责加载、保存和验证配置"""

    CONFIG_FILE = "config.yaml"
    EXAMPLE_FILE = "config_example.yaml"

    @staticmethod
    def load() -> dict:
        """
        加载配置文件
        首次运行时自动从模板复制
        """
        if not os.path.exists(ConfigLoader.CONFIG_FILE):
            if os.path.exists(ConfigLoader.EXAMPLE_FILE):
                shutil.copy(ConfigLoader.EXAMPLE_FILE, ConfigLoader.CONFIG_FILE)
            else:
                return ConfigLoader.get_default()

        with open(ConfigLoader.CONFIG_FILE, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            return config if config else ConfigLoader.get_default()

    @staticmethod
    def save(config: dict):
        """保存配置到文件"""
        with open(ConfigLoader.CONFIG_FILE, "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)

    @staticmethod
    def get_default() -> dict:
        """获取默认配置"""
        return {
            "api": {
                "base_url": "https://api.openai.com/v1",
                "api_key": "",
                "model": "gpt-4o-mini",
                "max_tokens": 2048,
            },
            "chat": {
                "context_limit": 128000,
                "compress_threshold": 0.8,
                "temperature": 0.7,
            },
            "persona": {
                "name": "皮卡丘",
                "system_prompt": "你是一只可爱的桌面宠物。",
                "user_preferences": [],
            },
            "ui": {"pet_size": 180, "dialog_interval": 5000},
            "history": {"auto_save": True, "file": "data/chat_history.json"},
        }

    @staticmethod
    def validate(config: dict) -> list:
        """
        验证配置
        返回错误信息列表
        """
        errors = []
        if not config.get("api", {}).get("api_key"):
            errors.append("API Key 未配置")
        if not config.get("api", {}).get("base_url"):
            errors.append("API 地址未配置")
        if not config.get("api", {}).get("model"):
            errors.append("模型未配置")
        return errors