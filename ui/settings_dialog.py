"""设置对话框模块 - 修复所有问题"""
import os
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QDialog, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QMessageBox, QPushButton,
    QPlainTextEdit, QSpinBox, QTabWidget, QVBoxLayout, QWidget,
    QButtonGroup, QRadioButton, QScrollArea, QAbstractItemView,
    QDialogButtonBox, QFormLayout,
)
from utils.config_loader import ConfigLoader
from utils.todo_storage import TodoStorage


def get_system_font_family():
    """获取跨平台字体族名称（用于样式表）"""
    if sys.platform == 'darwin':  # macOS
        return "'PingFang SC', '-apple-system', 'Helvetica Neue', sans-serif"
    elif sys.platform == 'win32':  # Windows
        return "'Microsoft YaHei UI', '微软雅黑', sans-serif"
    else:  # Linux 等
        return "'Noto Sans CJK SC', 'WenQuanYi Micro Hei', sans-serif"

FONT_FAMILY = get_system_font_family()


class InfoDialog(QDialog):
    """自定义提示对话框 - 跨平台一致的视觉效果"""

    # 设计系统颜色常量
    PRIMARY = "#5B8DEF"
    PRIMARY_HOVER = "#4A7FE0"
    TEXT_PRIMARY = "#1E293B"
    TEXT_SECONDARY = "#64748B"
    BG_MAIN = "#FFFFFF"
    BORDER = "#E2E8F0"

    def __init__(self, title: str, message: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(320, 140)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        # 设置窗口图标
        icon_path = "assets/icon.png"
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {self.BG_MAIN};
                border-radius: 12px;
            }}
            QLabel {{
                color: {self.TEXT_PRIMARY};
                font-family: {FONT_FAMILY};
                font-size: 14px;
                background: transparent;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 20)

        # 消息文本
        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        msg_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(msg_label)

        layout.addStretch()

        # 确认按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        ok_btn = QPushButton("确定")
        ok_btn.setFixedSize(80, 32)
        ok_btn.setCursor(Qt.PointingHandCursor)
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.PRIMARY};
                color: white;
                border: none;
                border-radius: 6px;
                font-family: {FONT_FAMILY};
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {self.PRIMARY_HOVER};
            }}
        """)
        ok_btn.clicked.connect(self.accept)

        btn_layout.addWidget(ok_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)


class SettingsDialog(QDialog):
    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("设置")
        self.setMinimumSize(440, 500)
        self.resize(440, 560)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        # 设置窗口图标
        icon_path = "assets/icon.png"
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # 现代化样式 - 确保 macOS 兼容性
        self.setStyleSheet(f"""
            QDialog {{
                background-color: #FAFAFA;
                font-family: {FONT_FAMILY};
            }}
            QWidget {{
                background-color: transparent;
                color: #333;
            }}
            QLabel {{
                color: #333;
                font-size: 13px;
                background: transparent;
            }}
            QLineEdit {{
                padding: 10px 14px;
                border: 1px solid #E8E8E8;
                border-radius: 8px;
                background: white;
                font-size: 13px;
                color: #333;
            }}
            QLineEdit:focus {{
                border: 2px solid #FFD93D;
                padding: 9px 13px;
            }}
            QLineEdit::placeholder {{
                color: #BBB;
            }}
            QPlainTextEdit {{
                padding: 10px;
                border: 1px solid #E8E8E8;
                border-radius: 8px;
                background: white;
                font-size: 13px;
                color: #333;
            }}
            QPlainTextEdit:focus {{
                border: 2px solid #FFD93D;
            }}
            QListWidget {{
                border: 1px solid #E8E8E8;
                border-radius: 8px;
                background: white;
                font-size: 13px;
                padding: 4px;
                color: #333;
            }}
            QListWidget::item {{
                padding: 6px 10px;
                min-height: 22px;
                border-radius: 4px;
                color: #333;
                background: transparent;
            }}
            QListWidget::item:selected {{
                background: #FFF9E6;
                color: #333;
            }}
            QListWidget::item:hover {{
                background: #FFFBF0;
            }}
            QTabWidget::pane {{
                border: 1px solid #E8E8E8;
                border-radius: 10px;
                background: white;
                margin-top: -1px;
            }}
            QTabWidget {{
                background: transparent;
            }}
            QTabBar {{
                background: transparent;
            }}
            QTabBar::tab {{
                padding: 10px 24px;
                background: #F5F5F5;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 2px;
                font-size: 13px;
                color: #666;
            }}
            QTabBar::tab:selected {{
                background: white;
                border-bottom: 2px solid #FFD93D;
                color: #333;
                font-weight: 500;
            }}
            QTabBar::tab:hover:!selected {{
                background: #EBEBEB;
            }}
            QComboBox {{
                padding: 10px 14px;
                border: 1px solid #E8E8E8;
                border-radius: 8px;
                background: white;
                font-size: 13px;
                color: #333;
            }}
            QComboBox:focus {{
                border: 2px solid #FFD93D;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            QComboBox QAbstractItemView {{
                background: white;
                color: #333;
                selection-background-color: #FFF9E6;
            }}
            QRadioButton {{
                font-size: 13px;
                color: #333;
                spacing: 8px;
                background: transparent;
            }}
            QRadioButton::indicator {{
                width: 18px;
                height: 18px;
            }}
            QRadioButton::indicator:checked {{
                background: #FFD93D;
                border-radius: 9px;
                border: 2px solid #FFC107;
            }}
            QRadioButton::indicator:unchecked {{
                background: white;
                border: 2px solid #DDD;
                border-radius: 9px;
            }}
            QCheckBox {{
                font-size: 13px;
                color: #333;
                spacing: 8px;
                background: transparent;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid #DDD;
                background: white;
            }}
            QCheckBox::indicator:checked {{
                background: #FFD93D;
                border-color: #FFC107;
            }}
            QPushButton {{
                padding: 10px 20px;
                border: 1px solid #E8E8E8;
                border-radius: 8px;
                background: white;
                font-size: 13px;
                color: #333;
            }}
            QPushButton:hover {{
                background: #F5F5F5;
                border-color: #DDD;
            }}
            QPushButton:pressed {{
                background: #EBEBEB;
            }}
            QSpinBox {{
                padding: 8px 12px;
                border: 1px solid #E8E8E8;
                border-radius: 8px;
                background: white;
                font-size: 13px;
                color: #333;
            }}
            QSpinBox:focus {{
                border: 2px solid #FFD93D;
            }}
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background: #F5F5F5;
                width: 10px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background: #DDD;
                border-radius: 5px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: #CCC;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 16, 20, 16)

        tabs = QTabWidget()

        # === 基础设置 ===
        basic_scroll = QScrollArea()
        basic_scroll.setWidgetResizable(True)
        basic_scroll.setFrameShape(QScrollArea.NoFrame)
        basic_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        basic_content = QWidget()
        basic_layout = QVBoxLayout(basic_content)
        basic_layout.setSpacing(8)

        # API 配置标题
        api_title = QLabel("⚡ API 配置")
        api_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #333; margin-top: 4px;")
        basic_layout.addWidget(api_title)

        self.api_url_input = QLineEdit()
        self.api_url_input.setText(self.config.get("api", {}).get("base_url", ""))
        self.api_url_input.setPlaceholderText("API 地址 (如: https://api.openai.com/v1)")
        basic_layout.addWidget(self.api_url_input)

        self.api_key_input = QLineEdit()
        self.api_key_input.setText(self.config.get("api", {}).get("api_key", ""))
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("API Key")
        basic_layout.addWidget(self.api_key_input)

        self.model_input = QLineEdit()
        self.model_input.setText(self.config.get("api", {}).get("model", "gpt-4o-mini"))
        self.model_input.setPlaceholderText("模型名称 (如: gpt-4o-mini)")
        basic_layout.addWidget(self.model_input)

        # 人设配置标题
        persona_title = QLabel("🎭 人设配置")
        persona_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #333; margin-top: 12px;")
        basic_layout.addWidget(persona_title)

        # 固定宠物名字显示
        from core.persona import DEFAULT_NAME
        name_label = QLabel(f"宠物名字: {DEFAULT_NAME}")
        name_label.setStyleSheet("color: #666; font-size: 13px; padding: 8px 0;")
        basic_layout.addWidget(name_label)

        # 人设提示词前缀（固定不可编辑）
        prompt_prefix_label = QLabel("人设: 你是一个电气老鼠宠物，你的主要职责是：")
        prompt_prefix_label.setStyleSheet("color: #666; font-size: 12px; background: #F5F5F5; padding: 8px; border-radius: 4px; margin-top: 4px;")
        prompt_prefix_label.setWordWrap(True)
        basic_layout.addWidget(prompt_prefix_label)

        # 主要职责输入框
        duties_label = QLabel("主要职责:")
        duties_label.setStyleSheet("color: #666; font-size: 12px; margin-top: 4px;")
        basic_layout.addWidget(duties_label)

        self.duties_input = QPlainTextEdit()
        self.duties_input.setPlainText(self.config.get("persona", {}).get("duties", ""))
        self.duties_input.setMinimumHeight(60)
        self.duties_input.setPlaceholderText("陪伴用户、提醒休息、聊天解闷...")
        basic_layout.addWidget(self.duties_input)

        # 用户画像（多维度）
        from core.persona import USER_PROFILE_DIMENSIONS, DIMENSION_DESCRIPTIONS

        profile_title = QLabel("📋 用户画像")
        profile_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #333; margin-top: 12px;")
        basic_layout.addWidget(profile_title)

        profile_hint = QLabel("填写你对用户的了解，帮助宠物更好地理解和服务用户")
        profile_hint.setStyleSheet("color: #999; font-size: 11px; margin-bottom: 4px;")
        basic_layout.addWidget(profile_hint)

        self.profile_inputs = {}
        user_profile = self.config.get("persona", {}).get("user_profile", {})

        for dim_key, dim_name in USER_PROFILE_DIMENSIONS.items():
            dim_label = QLabel(f"{dim_name}:")
            dim_label.setStyleSheet("color: #666; font-size: 12px; margin-top: 6px;")
            basic_layout.addWidget(dim_label)

            dim_hint = QLabel(DIMENSION_DESCRIPTIONS.get(dim_key, ""))
            dim_hint.setStyleSheet("color: #AAA; font-size: 10px;")
            basic_layout.addWidget(dim_hint)

            dim_input = QPlainTextEdit()
            dim_input.setPlainText(user_profile.get(dim_key, ""))
            dim_input.setMinimumHeight(60)
            dim_input.setPlaceholderText(f"描述用户的{dim_name}...")
            basic_layout.addWidget(dim_input)

            self.profile_inputs[dim_key] = dim_input

        basic_layout.addStretch()
        basic_scroll.setWidget(basic_content)
        tabs.addTab(basic_scroll, "基础")

        # === 状态配置 ===
        state_scroll = QScrollArea()
        state_scroll.setWidgetResizable(True)
        state_scroll.setFrameShape(QScrollArea.NoFrame)
        state_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        state_content = QWidget()
        state_layout = QVBoxLayout(state_content)
        state_layout.setSpacing(10)

        # 宠物尺寸
        size_title = QLabel("📐 宠物尺寸")
        size_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #333;")
        state_layout.addWidget(size_title)

        # 预设按钮 + 数字输入框
        size_btn_layout = QHBoxLayout()
        self.size_small_btn = QPushButton("小")
        self.size_medium_btn = QPushButton("中")
        self.size_large_btn = QPushButton("大")
        for btn in [self.size_small_btn, self.size_medium_btn, self.size_large_btn]:
            btn.setFixedHeight(32)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton {
                    background: #F5F5F5;
                    color: #666;
                    border: 1px solid #E0E0E0;
                    border-radius: 6px;
                    font-size: 13px;
                    padding: 0 16px;
                }
                QPushButton:checked {
                    background: #FFD93D;
                    color: #333;
                    border-color: #FFC107;
                }
                QPushButton:hover:!checked {
                    background: #EBEBEB;
                }
            """)
            size_btn_layout.addWidget(btn)
        self.size_small_btn.clicked.connect(lambda: self._on_size_preset(60))
        self.size_medium_btn.clicked.connect(lambda: self._on_size_preset(100))
        self.size_large_btn.clicked.connect(lambda: self._on_size_preset(160))
        size_btn_layout.addStretch()
        state_layout.addLayout(size_btn_layout)

        # 数字输入框
        size_input_layout = QHBoxLayout()
        size_input_label = QLabel("自定义:")
        size_input_label.setStyleSheet("color: #666; font-size: 13px;")
        size_input_layout.addWidget(size_input_label)
        self.pet_size_input = QSpinBox()
        self.pet_size_input.setRange(50, 300)
        self.pet_size_input.setSuffix(" px")
        self.pet_size_input.setFixedWidth(100)
        self.pet_size_input.setStyleSheet("""
            QSpinBox {
                padding: 6px 10px;
                border: 1px solid #E8E8E8;
                border-radius: 6px;
                background: white;
                font-size: 13px;
            }
            QSpinBox:focus {
                border: 2px solid #FFD93D;
            }
        """)
        current_size = self.config.get("ui", {}).get("pet_size", 100)
        self.pet_size_input.setValue(current_size)
        self.pet_size_input.valueChanged.connect(self._on_size_changed)
        size_input_layout.addWidget(self.pet_size_input)
        size_input_layout.addStretch()
        state_layout.addLayout(size_input_layout)

        # 初始化预设按钮状态
        self._update_size_preset_btn(current_size)

        # 聊天窗口尺寸
        chat_size_title = QLabel("💬 聊天窗口尺寸")
        chat_size_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #333; margin-top: 12px;")
        state_layout.addWidget(chat_size_title)

        chat_size_group = QButtonGroup(self)
        self.chat_size_small = QRadioButton("小 (520px)")
        self.chat_size_medium = QRadioButton("中 (660px)")
        self.chat_size_large = QRadioButton("大 (1000px)")
        chat_size_group.addButton(self.chat_size_small, 0)
        chat_size_group.addButton(self.chat_size_medium, 1)
        chat_size_group.addButton(self.chat_size_large, 2)

        current_chat_size = self.config.get("ui", {}).get("chat_window_size", "medium")
        if current_chat_size == "small":
            self.chat_size_small.setChecked(True)
        elif current_chat_size == "large":
            self.chat_size_large.setChecked(True)
        else:
            self.chat_size_medium.setChecked(True)

        self.chat_size_group = chat_size_group

        chat_size_layout = QHBoxLayout()
        chat_size_layout.addWidget(self.chat_size_small)
        chat_size_layout.addWidget(self.chat_size_medium)
        chat_size_layout.addWidget(self.chat_size_large)
        chat_size_layout.addStretch()
        state_layout.addLayout(chat_size_layout)

        # 休息提醒配置
        rest_title = QLabel("⏰ 休息提醒配置")
        rest_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #333; margin-top: 16px;")
        state_layout.addWidget(rest_title)

        # 启用开关
        self.rest_enabled_cb = QRadioButton("启用休息提醒")
        rest_config = self.config.get("rest_reminder", {})
        self.rest_enabled_cb.setChecked(rest_config.get("enabled", False))
        self.rest_enabled_cb.setStyleSheet("font-size: 13px; color: #333;")
        state_layout.addWidget(self.rest_enabled_cb)

        # 提醒间隔
        interval_layout = QHBoxLayout()
        interval_label = QLabel("提醒间隔:")
        interval_label.setStyleSheet("color: #666; font-size: 12px;")
        interval_label.setFixedWidth(70)
        interval_layout.addWidget(interval_label)

        self.rest_interval_combo = QComboBox()
        self.rest_interval_combo.addItems(["30 分钟", "1 小时", "2 小时", "3 小时"])
        current_interval = rest_config.get("interval", 3600)
        if current_interval == 1800:
            self.rest_interval_combo.setCurrentIndex(0)
        elif current_interval == 3600:
            self.rest_interval_combo.setCurrentIndex(1)
        elif current_interval == 7200:
            self.rest_interval_combo.setCurrentIndex(2)
        elif current_interval == 10800:
            self.rest_interval_combo.setCurrentIndex(3)
        else:
            self.rest_interval_combo.setCurrentIndex(1)  # 默认 1 小时
        self.rest_interval_combo.setStyleSheet("""
            QComboBox {
                padding: 6px 10px;
                border: 1px solid #E8E8E8;
                border-radius: 6px;
                background: white;
                font-size: 12px;
                min-width: 100px;
            }
        """)
        interval_layout.addWidget(self.rest_interval_combo)
        interval_layout.addStretch()
        state_layout.addLayout(interval_layout)

        # 提醒内容
        rest_msg_label = QLabel("提醒内容:")
        rest_msg_label.setStyleSheet("color: #666; font-size: 12px; margin-top: 8px;")
        state_layout.addWidget(rest_msg_label)

        self.rest_message_input = QLineEdit()
        rest_config = self.config.get("rest_reminder", {})
        self.rest_message_input.setText(rest_config.get("message", "⏰ 该休息啦！起来活动一下吧~"))
        self.rest_message_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #E8E8E8;
                border-radius: 6px;
                background: white;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 2px solid #FFD93D;
            }
        """)
        state_layout.addWidget(self.rest_message_input)

        # 待办提醒配置
        todo_title = QLabel("📝 待办提醒配置")
        todo_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #333; margin-top: 20px;")
        state_layout.addWidget(todo_title)

        todo_config = self.config.get("todo_reminder", {})
        
        # 待办列表
        self.todo_list = QListWidget()
        self.todo_list.setMaximumHeight(120)
        self.todo_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #E8E8E8;
                border-radius: 8px;
                background: white;
                font-size: 12px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 6px 10px;
                border-radius: 4px;
            }
        """)
        
        # 加载待办事项（从文件中获取）
        todos = TodoStorage.load_todos()
        for todo in todos:
            content = todo.get("content", "")
            time = todo.get("time", "")
            done = todo.get("done", False)
            item_text = f"[{'✓' if done else '○'}] {content} @ {time}"
            self.todo_list.addItem(item_text)

        # 连接选择变化信号，更新按钮文字
        self.todo_list.itemSelectionChanged.connect(self._update_complete_btn_text)
        state_layout.addWidget(self.todo_list)

        # 待办操作按钮
        todo_btn_layout = QHBoxLayout()
        
        add_todo_btn = QPushButton("+ 添加")
        add_todo_btn.setFixedHeight(28)
        add_todo_btn.setCursor(Qt.PointingHandCursor)
        add_todo_btn.setStyleSheet("""
            QPushButton {
                background: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                padding: 0 12px;
            }
            QPushButton:hover { background: #45a049; }
        """)
        add_todo_btn.clicked.connect(self._add_todo)
        todo_btn_layout.addWidget(add_todo_btn)

        del_todo_btn = QPushButton("删除")
        del_todo_btn.setFixedHeight(28)
        del_todo_btn.setCursor(Qt.PointingHandCursor)
        del_todo_btn.setStyleSheet("""
            QPushButton {
                background: #f44336;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                padding: 0 12px;
            }
            QPushButton:hover { background: #da190b; }
        """)
        del_todo_btn.clicked.connect(self._delete_todo)
        todo_btn_layout.addWidget(del_todo_btn)

        self.complete_todo_btn = QPushButton("完成")
        self.complete_todo_btn.setFixedHeight(28)
        self.complete_todo_btn.setCursor(Qt.PointingHandCursor)
        self.complete_todo_btn.setStyleSheet("""
            QPushButton {
                background: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                padding: 0 12px;
            }
            QPushButton:hover { background: #1976D2; }
        """)
        self.complete_todo_btn.clicked.connect(self._complete_todo)
        todo_btn_layout.addWidget(self.complete_todo_btn)
        
        todo_btn_layout.addStretch()
        state_layout.addLayout(todo_btn_layout)

        state_layout.addStretch()
        state_scroll.setWidget(state_content)
        tabs.addTab(state_scroll, "状态")

        # === 技能设置 ===
        ext_scroll = QScrollArea()
        ext_scroll.setWidgetResizable(True)
        ext_scroll.setFrameShape(QScrollArea.NoFrame)
        ext_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        ext_content = QWidget()
        ext_layout = QVBoxLayout(ext_content)
        ext_layout.setSpacing(10)

        # 技能配置
        skills_title = QLabel("🔧 技能配置")
        skills_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #333;")
        ext_layout.addWidget(skills_title)

        skills_hint = QLabel("配置技能模块目录，AI将自动加载目录中的技能")
        skills_hint.setStyleSheet("color: #999; font-size: 11px; margin-bottom: 4px;")
        ext_layout.addWidget(skills_hint)

        # 启用技能
        self.skills_enabled_cb = QRadioButton("启用技能系统")
        self.skills_enabled_cb.setChecked(self.config.get("skills", {}).get("enabled", True))
        self.skills_enabled_cb.setStyleSheet("font-size: 13px; color: #333;")
        ext_layout.addWidget(self.skills_enabled_cb)

        # 技能目录
        skills_dir_label = QLabel("技能目录:")
        skills_dir_label.setStyleSheet("color: #666; font-size: 12px; margin-top: 8px;")
        ext_layout.addWidget(skills_dir_label)

        skills_dir_layout = QHBoxLayout()
        self.skills_dir_input = QLineEdit()
        self.skills_dir_input.setText(self.config.get("skills", {}).get("directory", "skills"))
        self.skills_dir_input.setPlaceholderText("skills")
        skills_dir_layout.addWidget(self.skills_dir_input)

        browse_skills_btn = QPushButton("浏览")
        browse_skills_btn.setFixedWidth(70)
        browse_skills_btn.setFixedHeight(36)
        browse_skills_btn.setCursor(Qt.PointingHandCursor)
        browse_skills_btn.setStyleSheet(f"""
            QPushButton {{
                background: white;
                color: #333;
                border: 1px solid #E8E8E8;
                border-radius: 8px;
                font-size: 13px;
                font-family: {FONT_FAMILY};
            }}
            QPushButton:hover {{ background: #F5F5F5; border-color: #D0D0D0; }}
        """)
        browse_skills_btn.clicked.connect(self._browse_skills_dir)
        skills_dir_layout.addWidget(browse_skills_btn)
        ext_layout.addLayout(skills_dir_layout)

        # 已加载技能列表
        loaded_title = QLabel("已加载技能:")
        loaded_title.setStyleSheet("color: #666; font-size: 12px; margin-top: 12px;")
        ext_layout.addWidget(loaded_title)

        self.skills_list = QListWidget()
        self.skills_list.setMaximumHeight(120)
        self.skills_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #E8E8E8;
                border-radius: 8px;
                background: white;
                font-size: 13px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 6px 10px;
                border-radius: 4px;
            }
        """)
        # 加载已有技能
        from core.persona import load_skills
        skills = load_skills(self.config.get("skills", {}).get("directory", "skills"))
        for skill_name, skill_info in skills.items():
            desc = skill_info.get("description", "")[:50]
            item_text = f"{skill_name}: {desc}..." if len(skill_info.get("description", "")) > 50 else f"{skill_name}: {desc}"
            self.skills_list.addItem(item_text if desc else skill_name)
        ext_layout.addWidget(self.skills_list)

        # MCP 配置（JSON 格式）
        mcp_title = QLabel("🔌 MCP 配置")
        mcp_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #333; margin-top: 16px;")
        ext_layout.addWidget(mcp_title)

        mcp_hint = QLabel("Model Context Protocol - 使用 JSON 格式配置 MCP 服务器")
        mcp_hint.setStyleSheet("color: #999; font-size: 11px; margin-bottom: 4px;")
        ext_layout.addWidget(mcp_hint)

        self.mcp_enabled_cb = QRadioButton("启用 MCP")
        mcp_config = self.config.get("mcp", {})
        self.mcp_enabled_cb.setChecked(mcp_config.get("enabled", False))
        self.mcp_enabled_cb.setStyleSheet("font-size: 13px; color: #333;")
        ext_layout.addWidget(self.mcp_enabled_cb)

        mcp_json_label = QLabel("MCP 服务器配置 (JSON):")
        mcp_json_label.setStyleSheet("color: #666; font-size: 12px; margin-top: 8px;")
        ext_layout.addWidget(mcp_json_label)

        self.mcp_json_input = QPlainTextEdit()
        self.mcp_json_input.setMinimumHeight(200)
        # 格式化显示 JSON
        import json
        servers = mcp_config.get("servers", [])
        if servers:
            formatted_json = json.dumps(servers, indent=2, ensure_ascii=False)
        else:
            # 默认示例配置
            default_mcp = [
                {
                    "name": "filesystem",
                    "transport": "stdio",
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
                    "enabled": False,
                    "description": "文件系统访问"
                },
                {
                    "name": "brave-search",
                    "transport": "stdio",
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-brave-search"],
                    "env": {"BRAVE_API_KEY": ""},
                    "enabled": False,
                    "description": "Brave 搜索"
                }
            ]
            formatted_json = json.dumps(default_mcp, indent=2, ensure_ascii=False)
        self.mcp_json_input.setPlainText(formatted_json)
        self.mcp_json_input.setPlaceholderText('[\n  {\n    "name": "server-name",\n    "transport": "stdio",\n    "command": "npx",\n    "args": ["-y", "@modelcontextprotocol/server-xxx"],\n    "enabled": true\n  }\n]')
        self.mcp_json_input.setStyleSheet("""
            QPlainTextEdit {
                padding: 10px;
                border: 1px solid #E8E8E8;
                border-radius: 8px;
                background: white;
                font-size: 12px;
                font-family: 'Consolas', 'Courier New', monospace;
                color: #333;
            }
            QPlainTextEdit:focus {
                border: 2px solid #FFD93D;
            }
        """)
        ext_layout.addWidget(self.mcp_json_input)

        # JSON 格式提示
        json_hint = QLabel("💡 点击保存时自动验证 JSON 格式")
        json_hint.setStyleSheet("color: #999; font-size: 11px; margin-top: 4px;")
        ext_layout.addWidget(json_hint)

        ext_layout.addStretch()
        ext_scroll.setWidget(ext_content)
        tabs.addTab(ext_scroll, "扩展")

        layout.addWidget(tabs)

        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedHeight(40)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #F5F5F5;
                color: #666;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                font-size: 14px;
            }
            QPushButton:hover { background: #EBEBEB; }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("✓ 保存并应用")
        save_btn.setFixedHeight(40)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FFD93D, stop:1 #FFC107);
                color: #333;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FFC107, stop:1 #FF9800); }
        """)
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def _browse_skills_dir(self):
        """浏览技能目录"""
        from PyQt5.QtWidgets import QFileDialog
        from core.persona import load_skills
        dir_path = QFileDialog.getExistingDirectory(self, "选择技能目录")
        if dir_path:
            self.skills_dir_input.setText(dir_path)
            # 自动加载技能列表
            self.skills_list.clear()
            skills = load_skills(dir_path)
            for skill_name, skill_info in skills.items():
                desc = skill_info.get("description", "")[:50]
                item_text = f"{skill_name}: {desc}..." if len(skill_info.get("description", "")) > 50 else f"{skill_name}: {desc}"
                self.skills_list.addItem(item_text if desc else skill_name)

    def _on_size_preset(self, size):
        """预设按钮点击"""
        self.pet_size_input.setValue(size)
        self._update_size_preset_btn(size)

    def _on_size_changed(self, size):
        """数字输入框值变化"""
        self._update_size_preset_btn(size)

    def _update_size_preset_btn(self, size):
        """更新预设按钮状态"""
        self.size_small_btn.setChecked(size <= 80)
        self.size_medium_btn.setChecked(80 < size <= 100)
        self.size_large_btn.setChecked(size > 100)

    def get_selected_size(self):
        """获取选中的宠物尺寸"""
        return self.pet_size_input.value()

    def get_chat_window_size(self):
        """获取选中的聊天窗口尺寸"""
        checked = self.chat_size_group.checkedId()
        sizes = ["small", "medium", "large"]
        return sizes[checked] if 0 <= checked < 3 else "medium"

    def _save(self):
        if not self.api_key_input.text().strip():
            QMessageBox.warning(self, "提示", "请输入 API Key")
            return

        # 检测 API 配置变更
        old_api = self.config.get("api", {})
        api_changed = (
            old_api.get("base_url") != self.api_url_input.text().strip() or
            old_api.get("api_key") != self.api_key_input.text().strip() or
            old_api.get("model") != self.model_input.text().strip()
        )

        self.config.setdefault("api", {})
        self.config["api"]["base_url"] = self.api_url_input.text().strip()
        self.config["api"]["api_key"] = self.api_key_input.text().strip()
        self.config["api"]["model"] = self.model_input.text().strip()

        self.config.setdefault("persona", {})
        from core.persona import DEFAULT_NAME
        self.config["persona"]["name"] = DEFAULT_NAME  # 固定名字
        self.config["persona"]["duties"] = self.duties_input.toPlainText()

        # 保存用户画像（多维度）
        from core.persona import USER_PROFILE_DIMENSIONS
        self.config["persona"]["user_profile"] = {}
        for dim_key in USER_PROFILE_DIMENSIONS:
            value = self.profile_inputs[dim_key].toPlainText()
            if value.strip():
                self.config["persona"]["user_profile"][dim_key] = value

        self.config.setdefault("ui", {})
        self.config["ui"]["pet_size"] = self.get_selected_size()
        self.config["ui"]["chat_window_size"] = self.get_chat_window_size()

        # 保存休息提醒配置
        self.config.setdefault("rest_reminder", {})
        self.config["rest_reminder"]["enabled"] = self.rest_enabled_cb.isChecked()
        
        # 解析间隔
        interval_map = {0: 1800, 1: 3600, 2: 7200, 3: 10800}
        self.config["rest_reminder"]["interval"] = interval_map.get(self.rest_interval_combo.currentIndex(), 3600)
        
        # 保存提醒内容（单条）
        self.config["rest_reminder"]["message"] = self.rest_message_input.text().strip() or "⏰ 该休息啦！"

        # 保存待办提醒配置（待办列表写入独立文件）
        self.config.setdefault("todo_reminder", {})
        self.config["todo_reminder"]["enabled"] = True
        
        # 从列表中收集待办事项
        todos = []
        for i in range(self.todo_list.count()):
            item_text = self.todo_list.item(i).text()
            # 解析格式: [○] 内容 @ 时间
            import re
            match = re.match(r'\[(\W)\]\s*(.+)\s*@\s*(.+)', item_text)
            if match:
                done = (match.group(1) == '✓')
                content = match.group(2).strip()
                time = match.group(3).strip()
                todos.append({"content": content, "time": time, "done": done})

        # 待办只写入 data/todos.json，不再保存在 config.yaml 中
        TodoStorage.save_todos(todos)
        if "todos" in self.config["todo_reminder"]:
            self.config["todo_reminder"].pop("todos", None)

        # 保存技能配置
        self.config.setdefault("skills", {})
        self.config["skills"]["enabled"] = self.skills_enabled_cb.isChecked()
        self.config["skills"]["directory"] = self.skills_dir_input.text().strip() or "skills"

        # 保存 MCP 配置
        self._save_mcp_config()

        ConfigLoader.save(self.config)

        # API 配置变更提示重启
        if api_changed:
            InfoDialog("提示", "API 配置已更新，重启应用后生效", self).exec_()

        self.accept()

    def _create_mcp_server_widget(self, server_config, is_enabled: bool, user_config: dict) -> QWidget:
        """创建单个 MCP 服务器配置组件"""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background: white;
                border: 1px solid #E8E8E8;
                border-radius: 8px;
            }
        """)
        layout = QVBoxLayout(widget)
        layout.setSpacing(6)
        layout.setContentsMargins(12, 10, 12, 10)

        server_name = server_config.name

        # 标题行：启用开关 + 名称
        header_layout = QHBoxLayout()

        enabled_cb = QRadioButton()
        enabled_cb.setChecked(is_enabled)
        enabled_cb.setFixedWidth(20)
        enabled_cb.setStyleSheet("QRadioButton::indicator { width: 16px; height: 16px; }")
        header_layout.addWidget(enabled_cb)

        name_label = QLabel(server_name)
        name_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #333; background: transparent;")
        header_layout.addWidget(name_label)

        # 描述
        desc = server_config.description
        if desc:
            desc_label = QLabel(f"  · {desc}")
            desc_label.setStyleSheet("color: #999; font-size: 11px; background: transparent;")
            header_layout.addWidget(desc_label)

        header_layout.addStretch()
        layout.addLayout(header_layout)

        # 环境变量配置（如 API Key）
        env_configs = server_config.env
        env_inputs = {}

        if env_configs:
            env_widget = QWidget()
            env_widget.setStyleSheet("background: transparent;")
            env_layout = QVBoxLayout(env_widget)
            env_layout.setSpacing(4)
            env_layout.setContentsMargins(26, 0, 0, 0)

            for env_key, env_default in env_configs.items():
                env_row = QHBoxLayout()
                env_label = QLabel(f"{env_key}:")
                env_label.setStyleSheet("color: #666; font-size: 11px; background: transparent;")
                env_label.setFixedWidth(120)
                env_row.addWidget(env_label)

                env_input = QLineEdit()
                # 从用户配置中读取
                user_env = user_config.get("env", {})
                env_input.setText(user_env.get(env_key, ""))
                env_input.setPlaceholderText(f"输入 {env_key}")
                env_input.setEchoMode(QLineEdit.Password)
                env_input.setStyleSheet("""
                    QLineEdit {
                        padding: 6px 10px;
                        border: 1px solid #E0E0E0;
                        border-radius: 4px;
                        background: #FAFAFA;
                        font-size: 12px;
                    }
                    QLineEdit:focus { border-color: #FFD93D; }
                """)
                env_row.addWidget(env_input)
                env_layout.addLayout(env_row)
                env_inputs[env_key] = env_input

            layout.addWidget(env_widget)

        # 存储控件引用
        widget.enabled_cb = enabled_cb
        widget.env_inputs = env_inputs
        widget.server_name = server_name

        return widget

    def _on_mcp_enabled_changed(self, enabled: bool):
        """MCP 总开关状态变化"""
        self._update_mcp_status()

    def _update_mcp_status(self):
        """更新 MCP 状态提示"""
        if self.mcp_enabled_cb.isChecked():
            enabled_count = sum(1 for w in self.mcp_server_widgets.values() if w.enabled_cb.isChecked())
            self.mcp_status_label.setText(f"✓ MCP 已启用，{enabled_count} 个服务器将连接")
            self.mcp_status_label.setStyleSheet("color: #4CAF50; font-size: 11px; margin-top: 8px;")
        else:
            self.mcp_status_label.setText("○ MCP 未启用")
            self.mcp_status_label.setStyleSheet("color: #999; font-size: 11px; margin-top: 8px;")

    def _add_custom_mcp_server(self):
        """添加自定义 MCP 服务器"""
        from PyQt5.QtWidgets import QDialogButtonBox

        dialog = QDialog(self)
        dialog.setWindowTitle("添加 MCP 服务器")
        dialog.setMinimumWidth(400)
        dialog.setStyleSheet(self.styleSheet())

        layout = QVBoxLayout(dialog)

        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setSpacing(10)

        # 名称
        name_layout = QHBoxLayout()
        name_label = QLabel("名称:")
        name_label.setFixedWidth(80)
        name_input = QLineEdit()
        name_input.setPlaceholderText("my-server")
        name_layout.addWidget(name_label)
        name_layout.addWidget(name_input)
        form_layout.addLayout(name_layout)

        # 传输类型
        transport_layout = QHBoxLayout()
        transport_label = QLabel("传输类型:")
        transport_label.setFixedWidth(80)
        transport_combo = QComboBox()
        transport_combo.addItems(["stdio", "sse"])
        transport_layout.addWidget(transport_label)
        transport_layout.addWidget(transport_combo)
        form_layout.addLayout(transport_layout)

        # 命令
        cmd_layout = QHBoxLayout()
        cmd_label = QLabel("命令:")
        cmd_label.setFixedWidth(80)
        cmd_input = QLineEdit()
        cmd_input.setPlaceholderText("npx")
        cmd_layout.addWidget(cmd_label)
        cmd_layout.addWidget(cmd_input)
        form_layout.addLayout(cmd_layout)

        # 参数
        args_layout = QHBoxLayout()
        args_label = QLabel("参数:")
        args_label.setFixedWidth(80)
        args_input = QLineEdit()
        args_input.setPlaceholderText("-y, @modelcontextprotocol/server-xxx")
        args_layout.addWidget(args_label)
        args_layout.addWidget(args_input)
        form_layout.addLayout(args_layout)

        # 描述
        desc_layout = QHBoxLayout()
        desc_label = QLabel("描述:")
        desc_label.setFixedWidth(80)
        desc_input = QLineEdit()
        desc_input.setPlaceholderText("服务器描述")
        desc_layout.addWidget(desc_label)
        desc_layout.addWidget(desc_input)
        form_layout.addLayout(desc_layout)

        layout.addWidget(form_widget)

        # 按钮
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        layout.addWidget(btn_box)

        if dialog.exec_() == QDialog.Accepted:
            name = name_input.text().strip()
            if not name:
                QMessageBox.warning(self, "提示", "请输入服务器名称")
                return

            if name in self.mcp_server_widgets:
                QMessageBox.warning(self, "提示", "服务器名称已存在")
                return

            from core.mcp_config import MCPServerConfig
            args_text = args_input.text().strip()
            args = [a.strip() for a in args_text.split(",")] if args_text else []

            server_config = MCPServerConfig(
                name=name,
                transport=transport_combo.currentText(),
                command=cmd_input.text().strip() or None,
                args=args,
                description=desc_input.text().strip(),
                enabled=True,
            )

            server_widget = self._create_mcp_server_widget(server_config, True, {})
            self.mcp_servers_layout.addWidget(server_widget)
            self.mcp_server_widgets[name] = server_widget
            self._update_mcp_status()

    def _save_mcp_config(self):
        """保存 MCP 配置"""
        import json

        self.config.setdefault("mcp", {})
        self.config["mcp"]["enabled"] = self.mcp_enabled_cb.isChecked()

        # 解析 JSON 输入
        json_text = self.mcp_json_input.toPlainText().strip()
        
        if not json_text:
            self.config["mcp"]["servers"] = []
            return

        try:
            servers = json.loads(json_text)
            if not isinstance(servers, list):
                QMessageBox.warning(self, "JSON 格式错误", "MCP 配置应为数组格式")
                return
            self.config["mcp"]["servers"] = servers
        except json.JSONDecodeError as e:
            QMessageBox.warning(self, "JSON 格式错误", f"JSON 解析失败：{str(e)}")
            return

    def _add_todo(self):
        """添加待办事项"""
        from ui.chat_window import TodoDialog

        dialog = TodoDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            content, time_str = dialog.get_todo()
            if content and time_str:
                item_text = f"[○] {content} @ {time_str}"
                self.todo_list.addItem(item_text)
    
    def _delete_todo(self):
        """删除选中的待办事项"""
        current_row = self.todo_list.currentRow()
        if current_row >= 0:
            self.todo_list.takeItem(current_row)
            # 删除后更新按钮文字
            self._update_complete_btn_text()

    def _update_complete_btn_text(self):
        """根据选中待办的状态更新按钮文字"""
        current_row = self.todo_list.currentRow()
        if current_row < 0:
            self.complete_todo_btn.setText("完成")
            return

        item = self.todo_list.item(current_row)
        if not item:
            self.complete_todo_btn.setText("完成")
            return

        text = item.text()
        # 检查是否已完成（以 [✓] 开头）
        is_done = text.strip().startswith('[✓]')
        if is_done:
            self.complete_todo_btn.setText("撤销完成")
        else:
            self.complete_todo_btn.setText("完成")

    def _complete_todo(self):
        """完成/取消完成选中的待办事项"""
        current_row = self.todo_list.currentRow()
        if current_row < 0:
            return

        item = self.todo_list.item(current_row)
        if not item:
            return

        text = item.text()
        import re
        # 解析格式: [✓/○] 内容 @ 时间
        match = re.match(r'\[(\W)\]\s*(.+)\s*@\s*(.+)', text)
        if not match:
            return

        status = match.group(1)
        content = match.group(2).strip()
        time = match.group(3).strip()

        # 切换状态
        is_done = (status == '✓')
        new_status = '✓' if not is_done else '○'
        new_text = f"[{new_status}] {content} @ {time}"
        item.setText(new_text)
        # 更新按钮文字
        self._update_complete_btn_text()