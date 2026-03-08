"""待办事项存储工具

统一管理待办事项的读写，使用 data/todos.json 作为主要数据源，
并在首次加载时从 config.yaml 中的 todo_reminder.todos 迁移已有数据。
"""

import json
import os
from typing import List, Dict, Any

from utils.config_loader import ConfigLoader


class TodoStorage:
    """待办事项存储工具类"""

    TODO_FILE = os.path.join("data", "todos.json")

    @classmethod
    def _normalize_todo(cls, item: Any) -> Dict[str, Any]:
        """将任意结构的待办项规整为标准字典"""
        if not isinstance(item, dict):
            return {}

        content = str(item.get("content", "")).strip()
        time = str(item.get("time", "")).strip()
        done = bool(item.get("done", False))

        if not content or not time:
            return {}

        return {"content": content, "time": time, "done": done}

    @classmethod
    def load_todos(cls) -> List[Dict[str, Any]]:
        """加载所有待办事项

        优先从 data/todos.json 读取；若文件不存在，则尝试从 config.yaml
        的 todo_reminder.todos 中读取一次作为初始值。
        """
        # 优先读取 JSON 文件
        if os.path.exists(cls.TODO_FILE):
            try:
                with open(cls.TODO_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = []

            todos: List[Dict[str, Any]] = []
            if isinstance(data, list):
                for item in data:
                    normalized = cls._normalize_todo(item)
                    if normalized:
                        todos.append(normalized)
            return todos

        # 回退到 config.yaml 中的 todo_reminder
        config = ConfigLoader.load()
        todo_config = config.get("todo_reminder", {}) or {}
        raw_todos = todo_config.get("todos", []) or []

        todos: List[Dict[str, Any]] = []
        if isinstance(raw_todos, list):
            for item in raw_todos:
                normalized = cls._normalize_todo(item)
                if normalized:
                    todos.append(normalized)

        return todos

    @classmethod
    def save_todos(cls, todos: List[Dict[str, Any]]) -> None:
        """保存待办列表到 JSON 文件"""
        # 仅保存规整后的待办，避免写入非法结构
        cleaned: List[Dict[str, Any]] = []
        for item in todos:
            normalized = cls._normalize_todo(item)
            if normalized:
                cleaned.append(normalized)

        os.makedirs(os.path.dirname(cls.TODO_FILE), exist_ok=True)
        with open(cls.TODO_FILE, "w", encoding="utf-8") as f:
            json.dump(cleaned, f, ensure_ascii=False, indent=2)

    @classmethod
    def add_todo(cls, content: str, time: str) -> List[Dict[str, Any]]:
        """新增一条待办

        若相同 content+time 的待办已存在，则不重复添加，直接返回当前列表。
        """
        content = str(content).strip()
        time = str(time).strip()
        if not content or not time:
            return cls.load_todos()

        todos = cls.load_todos()
        for todo in todos:
            if todo.get("content") == content and todo.get("time") == time:
                # 已存在，直接返回
                return todos

        todos.append({"content": content, "time": time, "done": False})
        cls.save_todos(todos)
        return todos

