"""设置对话框模块 - 修复所有问题"""
import os
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QComboBox, QFileDialog, QInputDialog, QDialog, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QMessageBox, QPushButton,
    QPlainTextEdit, QSpinBox, QTabWidget, QVBoxLayout, QWidget,
    QButtonGroup, QRadioButton, QScrollArea, QAbstractItemView,
)
from utils.config_loader import ConfigLoader


class SettingsDialog(QDialog):
    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("设置")
        self.setMinimumSize(440, 500)
        self.resize(440, 560)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        # 现代化样式
        self.setStyleSheet("""
            QDialog {
                background-color: #FAFAFA;
                font-family: 'Microsoft YaHei UI', '微软雅黑', sans-serif;
            }
            QLabel {
                color: #333;
                font-size: 13px;
                background: transparent;
            }
            QLineEdit {
                padding: 10px 14px;
                border: 1px solid #E8E8E8;
                border-radius: 8px;
                background: white;
                font-size: 13px;
                color: #333;
            }
            QLineEdit:focus {
                border: 2px solid #FFD93D;
                padding: 9px 13px;
            }
            QLineEdit::placeholder {
                color: #BBB;
            }
            QPlainTextEdit {
                padding: 10px;
                border: 1px solid #E8E8E8;
                border-radius: 8px;
                background: white;
                font-size: 13px;
                color: #333;
            }
            QPlainTextEdit:focus {
                border: 2px solid #FFD93D;
            }
            QListWidget {
                border: 1px solid #E8E8E8;
                border-radius: 8px;
                background: white;
                font-size: 13px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 6px 10px;
                min-height: 22px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background: #FFF9E6;
                color: #333;
            }
            QListWidget::item:hover {
                background: #FFFBF0;
            }
            QTabWidget::pane {
                border: 1px solid #E8E8E8;
                border-radius: 10px;
                background: white;
                margin-top: -1px;
            }
            QTabBar::tab {
                padding: 10px 24px;
                background: #F5F5F5;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 2px;
                font-size: 13px;
                color: #666;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom: 2px solid #FFD93D;
                color: #333;
                font-weight: 500;
            }
            QTabBar::tab:hover:!selected {
                background: #EBEBEB;
            }
            QComboBox {
                padding: 10px 14px;
                border: 1px solid #E8E8E8;
                border-radius: 8px;
                background: white;
                font-size: 13px;
            }
            QComboBox:focus {
                border: 2px solid #FFD93D;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QRadioButton {
                font-size: 13px;
                color: #333;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
            QRadioButton::indicator:checked {
                background: #FFD93D;
                border-radius: 9px;
                border: 2px solid #FFC107;
            }
            QRadioButton::indicator:unchecked {
                background: white;
                border: 2px solid #DDD;
                border-radius: 9px;
            }
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

        state_layout.addStretch()
        state_scroll.setWidget(state_content)
        tabs.addTab(state_scroll, "状态")

        # === 扩展设置 ===
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
        browse_skills_btn.setStyleSheet("""
            QPushButton {
                background: white;
                color: #333;
                border: 1px solid #E8E8E8;
                border-radius: 8px;
                font-size: 13px;
                font-family: 'Microsoft YaHei UI', sans-serif;
            }
            QPushButton:hover { background: #F5F5F5; border-color: #D0D0D0; }
        """)
        browse_skills_btn.clicked.connect(self._browse_skills_dir)
        skills_dir_layout.addWidget(browse_skills_btn)
        ext_layout.addLayout(skills_dir_layout)

        # 已加载技能列表
        loaded_title = QLabel("已加载技能:")
        loaded_title.setStyleSheet("color: #666; font-size: 12px; margin-top: 12px;")
        ext_layout.addWidget(loaded_title)

        self.skills_list = QListWidget()
        self.skills_list.setMaximumHeight(150)
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

        # 保存技能配置
        self.config.setdefault("skills", {})
        self.config["skills"]["enabled"] = self.skills_enabled_cb.isChecked()
        self.config["skills"]["directory"] = self.skills_dir_input.text().strip() or "skills"

        ConfigLoader.save(self.config)

        # API 配置变更提示重启
        if api_changed:
            QMessageBox.information(self, "提示", "API 配置已更新，重启应用后生效")

        self.accept()