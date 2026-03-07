"""人设管理模块"""
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING
import os
import re
import json

from openai import OpenAI

if TYPE_CHECKING:
    from core.skill_tool import SkillToolChain


# 默认常量
DEFAULT_NAME = "皮卡丘"
DEFAULT_PROMPT_PREFIX = "你是一个电气老鼠宠物，你的主要职责是："
DEFAULT_DUTIES = "陪伴用户、聊天解闷"

# 用户偏好维度定义
USER_PROFILE_DIMENSIONS = {
    "daily_details": "日常细节",
    "emotional_response": "情绪反应",
    "value_choices": "价值选择",
    "social_circle": "社交圈层",
    "adversity_response": "逆境应对",
    "cognitive_pattern": "认知格局",
    "solitude_state": "独处状态",
}

# 维度描述（用于UI提示）
DIMENSION_DESCRIPTIONS = {
    "daily_details": "作息习惯、兴趣爱好、消费偏好等",
    "emotional_response": "情绪表达方式、压力反应、情感需求等",
    "value_choices": "人生优先级、决策倾向、道德观念等",
    "social_circle": "社交频率、人际关系、沟通风格等",
    "adversity_response": "面对困难的态度、应对策略、恢复能力等",
    "cognitive_pattern": "思维模式、学习方式、决策风格等",
    "solitude_state": "独处习惯、内心对话、自我认知等",
}


def build_system_prompt(user_duties: str = "") -> str:
    """构建完整人设提示词

    Args:
        user_duties: 用户自定义的主要职责描述

    Returns:
        完整的人设提示词
    """
    if not user_duties or not user_duties.strip():
        user_duties = DEFAULT_DUTIES
    return DEFAULT_PROMPT_PREFIX + user_duties.strip()


def parse_skill_frontmatter(content: str) -> Tuple[dict, str]:
    """解析 SKILL.md 的 YAML frontmatter

    Args:
        content: SKILL.md 文件内容

    Returns:
        (metadata_dict, markdown_body)
    """
    pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
    match = re.match(pattern, content, re.DOTALL)

    if not match:
        return {}, content

    frontmatter_str, body = match.groups()
    metadata = {}

    for line in frontmatter_str.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            # 跳过复杂嵌套字段
            if key not in ('metadata', 'compatibility'):
                metadata[key] = value

    return metadata, body


def load_skills(skills_dir: str = "skills") -> Dict[str, dict]:
    """加载 skills 目录中的技能（只支持 SKILL.md）

    Args:
        skills_dir: skills 目录路径

    Returns:
        技能字典 {skill_name: skill_info}
    """
    skills = {}
    if not os.path.exists(skills_dir):
        return skills

    for item in os.listdir(skills_dir):
        skill_path = os.path.join(skills_dir, item)
        skill_md = os.path.join(skill_path, "SKILL.md")

        if not os.path.isdir(skill_path):
            continue
        if not os.path.exists(skill_md):
            continue

        try:
            with open(skill_md, "r", encoding="utf-8") as f:
                content = f.read()

            metadata, body = parse_skill_frontmatter(content)

            skill_info = {
                "path": skill_path,
                "name": metadata.get("name", item),
                "description": metadata.get("description", ""),
                "license": metadata.get("license", ""),
                "body": body,
            }

            skills[item] = skill_info
        except Exception:
            continue

    return skills


def build_skills_prompt(skills: Dict[str, dict]) -> str:
    """构建技能提示词

    Args:
        skills: 技能字典

    Returns:
        技能提示词
    """
    if not skills:
        return ""

    lines = ["\n\n## 可用技能", ""]
    for skill_name, skill_info in skills.items():
        desc = skill_info.get("description", "")
        if desc:
            lines.append(f"- **{skill_name}**: {desc}")
        else:
            lines.append(f"- **{skill_name}**")

    lines.append("")
    lines.append("当用户的问题涉及上述技能时，你可以在回复中引用相关技能来提供更专业的帮助。")
    return "\n".join(lines)


class SkillLoader:
    """
    链式技能加载器
    
    支持链式调用加载技能：
    
    ```python
    loader = SkillLoader()
    skills = (loader
        .from_directory("skills")
        .from_directory("extra_skills")
        .filter(lambda s: s.get("enabled", True))
        .build())
    ```
    """
    
    def __init__(self):
        self._skills: Dict[str, dict] = {}
        self._load_order: List[str] = []
    
    def load(
        self,
        skill_key: str,
        skill_info: dict
    ) -> "SkillLoader":
        """
        加载单个技能
        
        Args:
            skill_key: 技能键名
            skill_info: 技能信息
            
        Returns:
            返回自身，支持链式调用
        """
        if skill_key not in self._skills:
            self._load_order.append(skill_key)
        self._skills[skill_key] = skill_info
        return self
    
    def load_dict(
        self,
        skills: Dict[str, dict]
    ) -> "SkillLoader":
        """
        从字典加载技能
        
        Args:
            skills: 技能字典
            
        Returns:
            返回自身，支持链式调用
        """
        for skill_key, skill_info in skills.items():
            self.load(skill_key, skill_info)
        return self
    
    def from_directory(
        self,
        directory: str
    ) -> "SkillLoader":
        """
        从目录加载技能
        
        Args:
            directory: 技能目录路径
            
        Returns:
            返回自身，支持链式调用
        """
        skills = load_skills(directory)
        return self.load_dict(skills)
    
    def from_directories(
        self,
        directories: List[str]
    ) -> "SkillLoader":
        """
        从多个目录加载技能
        
        Args:
            directories: 目录列表
            
        Returns:
            返回自身，支持链式调用
        """
        for directory in directories:
            self.from_directory(directory)
        return self
    
    def filter(
        self,
        predicate: callable
    ) -> "SkillLoader":
        """
        过滤技能
        
        Args:
            predicate: 过滤函数，接收 skill_info，返回 bool
            
        Returns:
            返回自身，支持链式调用
        """
        filtered = {}
        for key in self._load_order:
            if key in self._skills and predicate(self._skills[key]):
                filtered[key] = self._skills[key]
        self._skills = filtered
        self._load_order = list(filtered.keys())
        return self
    
    def map(
        self,
        transformer: callable
    ) -> "SkillLoader":
        """
        转换技能
        
        Args:
            transformer: 转换函数，接收 (skill_key, skill_info)，返回新的 skill_info
            
        Returns:
            返回自身，支持链式调用
        """
        for key in self._load_order:
            if key in self._skills:
                self._skills[key] = transformer(key, self._skills[key])
        return self
    
    def exclude(
        self,
        skill_keys: List[str]
    ) -> "SkillLoader":
        """
        排除指定技能
        
        Args:
            skill_keys: 要排除的技能键名列表
            
        Returns:
            返回自身，支持链式调用
        """
        for key in skill_keys:
            if key in self._skills:
                del self._skills[key]
                self._load_order.remove(key)
        return self
    
    def only(
        self,
        skill_keys: List[str]
    ) -> "SkillLoader":
        """
        只保留指定技能
        
        Args:
            skill_keys: 要保留的技能键名列表
            
        Returns:
            返回自身，支持链式调用
        """
        self._skills = {
            k: self._skills[k] 
            for k in skill_keys 
            if k in self._skills
        }
        self._load_order = [k for k in self._load_order if k in self._skills]
        return self
    
    def build(self) -> Dict[str, dict]:
        """
        构建并返回技能字典
        
        Returns:
            技能字典
        """
        return self._skills.copy()
    
    def to_tool_chain(self) -> "SkillToolChain":
        """
        转换为 SkillToolChain
        
        Returns:
            SkillToolChain 实例
        """
        from core.skill_tool import SkillToolChain
        return SkillToolChain().load_batch(self._skills)
    
    def clear(self) -> "SkillLoader":
        """
        清空已加载的技能
        
        Returns:
            返回自身，支持链式调用
        """
        self._skills.clear()
        self._load_order.clear()
        return self
    
    def __len__(self) -> int:
        """返回技能数量"""
        return len(self._skills)
    
    def __iter__(self):
        """支持迭代"""
        for key in self._load_order:
            yield key, self._skills[key]
    
    def __contains__(self, skill_key: str) -> bool:
        """检查技能是否存在"""
        return skill_key in self._skills


class PersonaManager:
    """人设管理器，负责管理 AI 人设和用户偏好"""

    def __init__(self, config: dict):
        self.config = config
        persona_config = config.get("persona", {})
        self.name = persona_config.get("name", DEFAULT_NAME)

        # 兼容旧配置: 优先使用 duties 构建，若无则使用 system_prompt
        if "duties" in persona_config:
            self.system_prompt = build_system_prompt(persona_config["duties"])
        elif "system_prompt" in persona_config:
            self.system_prompt = persona_config["system_prompt"]
        else:
            self.system_prompt = build_system_prompt("")

        # 用户画像（多维度）
        self.user_profile: Dict[str, str] = {}
        # 兼容旧配置
        old_preferences = persona_config.get("user_preferences", [])
        if isinstance(old_preferences, list) and old_preferences:
            # 将旧列表转换为描述字段
            self.user_profile["daily_details"] = "\n".join(f"- {p}" for p in old_preferences)
        elif "user_profile" in persona_config:
            self.user_profile = persona_config.get("user_profile", {})
            # 确保所有维度都存在
            for dim in USER_PROFILE_DIMENSIONS:
                if dim not in self.user_profile:
                    self.user_profile[dim] = ""

        # Skills 配置
        self.skills_dir = config.get("skills", {}).get("directory", "skills")
        self.skills_enabled = config.get("skills", {}).get("enabled", True)
        self._loaded_skills: Optional[Dict[str, dict]] = None
        self._skill_loader: Optional[SkillLoader] = None

    def get_skills(self) -> Dict[str, dict]:
        """获取加载的技能（懒加载）"""
        if self._loaded_skills is None and self.skills_enabled:
            self._loaded_skills = load_skills(self.skills_dir)
        return self._loaded_skills or {}

    def get_skill_loader(self) -> SkillLoader:
        """
        获取链式技能加载器（懒加载）
        
        Returns:
            SkillLoader 实例
        """
        if self._skill_loader is None:
            self._skill_loader = SkillLoader()
            if self.skills_enabled and self.skills_dir:
                self._skill_loader.from_directory(self.skills_dir)
        return self._skill_loader
    
    def reload_skills(self) -> "PersonaManager":
        """
        重新加载技能
        
        Returns:
            返回自身，支持链式调用
        """
        self._loaded_skills = None
        self._skill_loader = None
        return self
    
    def add_skill_directory(self, directory: str) -> "PersonaManager":
        """
        添加额外的技能目录
        
        Args:
            directory: 技能目录路径
            
        Returns:
            返回自身，支持链式调用
        """
        loader = self.get_skill_loader()
        loader.from_directory(directory)
        self._loaded_skills = loader.build()
        return self
    
    def filter_skills(self, predicate: callable) -> "PersonaManager":
        """
        过滤技能
        
        Args:
            predicate: 过滤函数
            
        Returns:
            返回自身，支持链式调用
        """
        loader = self.get_skill_loader()
        loader.filter(predicate)
        self._loaded_skills = loader.build()
        return self

    def get_system_message(self) -> dict:
        """
        获取完整的系统消息

        Returns:
            系统消息字典 {"role": "system", "content": "..."}
        """
        content = self.system_prompt

        # 添加用户画像
        profile_parts = []
        for dim_key, dim_name in USER_PROFILE_DIMENSIONS.items():
            value = self.user_profile.get(dim_key, "")
            if value and value.strip():
                profile_parts.append(f"**{dim_name}**:\n{value.strip()}")

        if profile_parts:
            content += "\n\n## 用户画像\n" + "\n\n".join(profile_parts)

        # 添加技能提示
        if self.skills_enabled:
            skills = self.get_skills()
            if skills:
                content += build_skills_prompt(skills)

        return {"role": "system", "content": content}

    def update_user_profile(self, dimension: str, value: str):
        """
        更新用户画像的某个维度

        Args:
            dimension: 维度键名
            value: 维度值
        """
        if dimension in USER_PROFILE_DIMENSIONS:
            self.user_profile[dimension] = value
            if "persona" not in self.config:
                self.config["persona"] = {}
            if "user_profile" not in self.config["persona"]:
                self.config["persona"]["user_profile"] = {}
            self.config["persona"]["user_profile"][dimension] = value

    def set_user_profile(self, profile: Dict[str, str]):
        """
        设置完整的用户画像

        Args:
            profile: 用户画像字典
        """
        self.user_profile = profile
        if "persona" not in self.config:
            self.config["persona"] = {}
        self.config["persona"]["user_profile"] = profile

    def set_duties(self, duties: str):
        """设置主要职责"""
        self.system_prompt = build_system_prompt(duties)
        if "persona" not in self.config:
            self.config["persona"] = {}
        self.config["persona"]["duties"] = duties

    def reset_to_default(self):
        """重置为默认人设"""
        self.name = DEFAULT_NAME
        self.system_prompt = build_system_prompt("")
        self.user_profile = {dim: "" for dim in USER_PROFILE_DIMENSIONS}
        self._loaded_skills = None
        self.config["persona"] = {
            "name": self.name,
            "duties": "",
            "user_profile": self.user_profile.copy(),
        }

    def to_dict(self) -> dict:
        """导出为字典"""
        return {
            "name": self.name,
            "system_prompt": self.system_prompt,
            "user_profile": self.user_profile.copy(),
            "skills": {
                "directory": self.skills_dir,
                "enabled": self.skills_enabled,
            },
        }

    def analyze_user_profile(self, messages: List[dict], api_config: dict) -> Dict[str, str]:
        """
        分析聊天记录生成用户画像

        Args:
            messages: 聊天记录列表
            api_config: API 配置

        Returns:
            用户画像字典，映射到各维度字段
        """
        if not messages:
            return {}

        # 构建 prompt
        dimensions_desc = "\n".join(
            f"- {key}: {DIMENSION_DESCRIPTIONS[key]}"
            for key in USER_PROFILE_DIMENSIONS
        )

        # 提取用户消息
        user_messages = [msg["content"] for msg in messages if msg["role"] == "user"]
        if not user_messages:
            return {}

        chat_text = "\n".join(f"用户: {msg}" for msg in user_messages[-50:])  # 最近50条

        prompt = f"""分析以下聊天记录，提取用户的特征画像。

用户画像维度：
{dimensions_desc}

现有用户画像：
{json.dumps(self.user_profile, ensure_ascii=False, indent=2)}

聊天记录：
{chat_text}

请根据聊天记录分析用户特征，返回 JSON 格式，仅包含有明确依据的字段。
格式示例：
{{"daily_details": "用户喜欢熬夜，偏好技术类内容", "emotional_response": "表达直接，情绪稳定"}}

仅返回 JSON，不要其他内容。"""

        try:
            client = OpenAI(
                base_url=api_config.get("base_url", "https://api.openai.com/v1"),
                api_key=api_config.get("api_key", ""),
            )
            response = client.chat.completions.create(
                model=api_config.get("model", "gpt-4o-mini"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.3,
            )

            result = response.choices[0].message.content.strip()
            # 提取 JSON
            if result.startswith("```"):
                result = re.sub(r"^```json?\s*", "", result)
                result = re.sub(r"\s*```$", "", result)

            profile = json.loads(result)

            # 只保留有效维度
            valid_profile = {}
            for key, value in profile.items():
                if key in USER_PROFILE_DIMENSIONS and isinstance(value, str):
                    valid_profile[key] = value

            return valid_profile

        except Exception:
            return {}