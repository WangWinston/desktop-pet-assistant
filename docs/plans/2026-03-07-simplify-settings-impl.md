# 设置界面简化 - 实现计划

## 概述

基于设计文档 `docs/plans/2026-03-07-simplify-settings-design.md`，简化桌面宠物设置界面。

## 实现步骤

### 步骤 1: 修改 core/persona.py

**目标**: 添加默认常量和构建人设提示词的函数

**变更内容**:

1. 在文件顶部添加常量：
```python
DEFAULT_NAME = "皮卡丘"
DEFAULT_PROMPT_PREFIX = "你是一个电气老鼠宠物，你的主要职责是："
DEFAULT_DUTIES = "陪伴用户、聊天解闷"
```

2. 添加 `build_system_prompt` 函数：
```python
def build_system_prompt(user_duties: str = "") -> str:
    """构建完整人设提示词"""
    if not user_duties or not user_duties.strip():
        user_duties = DEFAULT_DUTIES
    return DEFAULT_PROMPT_PREFIX + user_duties.strip()
```

3. 修改 `PersonaManager.__init__`:
   - 移除 `self.system_prompt` 直接读取
   - 改为读取 `duties` 字段并调用 `build_system_prompt`
   - 使用 `DEFAULT_NAME` 作为默认名字

4. 修改 `reset_to_default` 方法使用新常量

---

### 步骤 2: 修改 ui/settings_dialog.py

**目标**: 简化设置界面

**变更内容**:

#### 2.1 基础标签页 - 人设配置区域

**移除**:
- `self.name_input` 输入框及其相关代码（第176-179行）

**修改**:
- 将 `self.prompt_input` (QPlainTextEdit) 改为 `self.duties_input`
- 添加固定前缀提示标签：
  ```python
  prompt_prefix_label = QLabel("你是一个电气老鼠宠物，你的主要职责是：")
  prompt_prefix_label.setStyleSheet("color: #666; font-size: 12px; background: #F5F5F5; padding: 8px; border-radius: 4px;")
  prompt_prefix_label.setWordWrap(True)
  ```

**保留**:
- API 配置区域
- 用户偏好列表

#### 2.2 状态标签页

**移除**:
- "动画文件"配置区域（第369-389行）
- "对话文本"配置区域（第391-394行）
- `self.anim_input` 输入框
- `self.state_dialog_input` 输入框
- `_browse_animation` 方法
- `_save_state_config` 方法
- `_load_state_config` 方法中动画和对话相关代码

**保留**:
- 宠物尺寸设置
- 聊天窗口尺寸设置

#### 2.3 _save 方法修改

**移除**:
- `self.config["persona"]["name"]` 赋值（名字固定）
- `self.config["persona"]["system_prompt"]` 赋值

**添加**:
- `self.config["persona"]["duties"]` 赋值（从 `self.duties_input` 获取）

---

### 步骤 3: 更新配置文件

#### 3.1 修改 config.yaml

```yaml
persona:
  name: 皮卡丘
  duties: ""  # 用户自定义主要职责
  user_preferences: []
```

#### 3.2 修改 config_example.yaml

同上，保持示例配置与实际使用一致。

---

### 步骤 4: 验证测试

1. 启动应用，确认设置界面显示正确
2. 验证人设提示词生成正确
3. 验证聊天功能正常
4. 验证配置保存和加载正确

## 文件变更清单

| 文件 | 操作 |
|------|------|
| core/persona.py | 修改 |
| ui/settings_dialog.py | 修改 |
| config.yaml | 修改 |
| config_example.yaml | 修改 |

## 风险评估

- **低风险**: 界面简化不涉及核心逻辑变更
- **兼容性**: 旧配置文件中的 `system_prompt` 字段将被忽略，不影响运行

## 回滚方案

保留原 `system_prompt` 配置项的读取逻辑作为 fallback：
```python
# 兼容旧配置
if "system_prompt" in persona_config:
    self.system_prompt = persona_config["system_prompt"]
else:
    duties = persona_config.get("duties", "")
    self.system_prompt = build_system_prompt(duties)
```