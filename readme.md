# 桌面宠物 - 皮卡丘

一只可爱的桌面宠物，基于 PyQt5 构建，支持 AI 对话功能。

## 功能特性

- **桌面宠物展示** - 可爱的皮卡丘动画，支持拖拽移动
- **AI 对话** - 接入 OpenAI 兼容 API，支持智能对话
- **用户画像** - 多维度记录用户特征，提供个性化服务
- **技能系统** - 可扩展的技能模块，支持动态加载
- **休息提醒** - 定时提醒用户休息，保护健康

## 快速开始

### 环境要求

- Python 3.8+
- PyQt5

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置

1. 复制配置文件模板：
```bash
cp config_example.yaml config.yaml
```

2. 编辑 `config.yaml`，填入你的 API 配置：
```yaml
api:
  base_url: "https://api.openai.com/v1"
  api_key: "your-api-key-here"
  model: "gpt-4o-mini"
```

### 运行

```bash
python main.py
```

## 项目结构

```
├── main.py              # 主入口
├── config.yaml          # 配置文件
├── requirements.txt     # 依赖列表
├── core/
│   ├── persona.py       # 人设和用户画像管理
│   ├── chat.py          # AI 对话核心
│   ├── memory.py        # 上下文记忆
│   └── compressor.py    # 消息压缩
├── ui/
│   ├── pet.py           # 宠物窗口
│   ├── chat_window.py   # 聊天窗口
│   └── settings_dialog.py # 设置对话框
├── skills/              # 技能模块目录
│   └── weather/         # 天气查询示例
│       └── SKILL.md     # 技能定义文件
└── assets/              # 静态资源
    ├── pikaqiu/         # 皮卡丘动画
    └── click/           # 点击动画
```

## 用户画像维度

系统支持以下维度的用户画像，帮助宠物更好地理解和陪伴用户：

| 维度 | 说明 |
|------|------|
| 日常细节 | 作息习惯、兴趣爱好、消费偏好等 |
| 情绪反应 | 情绪表达方式、压力反应、情感需求等 |
| 价值选择 | 人生优先级、决策倾向、道德观念等 |
| 社交圈层 | 社交频率、人际关系、沟通风格等 |
| 逆境应对 | 面对困难的态度、应对策略、恢复能力等 |
| 认知格局 | 思维模式、学习方式、决策风格等 |
| 独处状态 | 独处习惯、内心对话、自我认知等 |

## 技能系统

基于 Agent Skill 规范，使用 `SKILL.md` 文件定义技能。

### 添加新技能

1. 在 `skills/` 目录下创建新文件夹，如 `skills/my-skill/`
2. 创建 `SKILL.md` 文件：

```markdown
---
name: my-skill
description: 技能描述，说明功能和适用场景
---

# 技能标题

## 使用场景
描述何时使用此技能。

## 执行步骤
1. 步骤一
2. 步骤二
```

### SKILL.md 格式要求

| 字段 | 必填 | 说明 |
|------|------|------|
| name | 是 | 技能名称，仅小写字母、数字、连字符 |
| description | 是 | 技能描述，1-1024 字符 |
| license | 否 | 许可证名称 |

### 技能目录结构

```
skills/
└── my-skill/
    ├── SKILL.md          # 必需
    ├── scripts/          # 可选：可执行脚本
    ├── references/       # 可选：参考文档
    └── assets/           # 可选：静态资源
```

### 启用技能

在 `config.yaml` 中配置：

```yaml
skills:
  enabled: true
  directory: "skills"
```

### 技能加载

系统启动时自动加载 skills 目录中的技能，将技能名称和描述注入系统提示，AI 可根据用户问题动态引用相关技能。

## 配置说明

```yaml
# API 配置
api:
  base_url: "API 地址"
  api_key: "API 密钥"
  model: "模型名称"
  max_tokens: 2048

# 对话配置
chat:
  context_limit: 128000    # 上下文长度限制
  compress_threshold: 0.8  # 压缩阈值
  temperature: 0.7         # 生成温度

# 人设配置
persona:
  name: "皮卡丘"
  duties: "主要职责描述"
  user_profile:            # 用户画像
    daily_details: ""
    emotional_response: ""
    value_choices: ""
    social_circle: ""
    adversity_response: ""
    cognitive_pattern: ""
    solitude_state: ""

# 技能配置
skills:
  enabled: true
  directory: "skills"

# UI 配置
ui:
  pet_size: 100            # 宠物尺寸
  chat_window_size: "medium"  # 聊天窗口尺寸
  dialog_interval: 5000    # 对话间隔
```

## 操作说明

- **拖拽移动** - 按住宠物拖拽到任意位置
- **右键菜单** - 右键点击宠物打开菜单
  - 聊天 - 打开聊天窗口
  - 设置 - 打开设置对话框
  - 退出 - 关闭程序
- **聊天窗口** - 点击设置按钮⚙打开设置，点击关闭按钮✕隐藏窗口

## 开发

### 扩展功能

项目采用模块化设计，易于扩展：

1. **添加新状态** - 在 `config.yaml` 的 `states` 中配置
2. **添加新技能** - 在 `skills/` 目录下创建新模块
3. **自定义人设** - 修改 `core/persona.py` 中的常量

### 代码风格

- 使用 Python 类型注解
- 遵循 PEP 8 规范

## 许可证

MIT License

## 致谢

本项目基于 [DeskTopPet](https://github.com/llq20133100095/DeskTopPet) 进行重构和扩展。