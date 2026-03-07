"""设置对话框模块 - 修复所有问题"""
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
        self.setMinimumSize(440, 680)
        self.resize(440, 720)
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
        basic_tab = QWidget()
        basic_layout = QVBoxLayout(basic_tab)
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

        self.name_input = QLineEdit()
        self.name_input.setText(self.config.get("persona", {}).get("name", "皮卡丘"))
        self.name_input.setPlaceholderText("宠物名字")
        basic_layout.addWidget(self.name_input)

        prompt_label = QLabel("人设提示词:")
        prompt_label.setStyleSheet("color: #666; font-size: 12px; margin-top: 4px;")
        basic_layout.addWidget(prompt_label)

        self.prompt_input = QPlainTextEdit()
        self.prompt_input.setPlainText(self.config.get("persona", {}).get("system_prompt", ""))
        self.prompt_input.setMinimumHeight(60)
        self.prompt_input.setPlaceholderText("设置宠物的人设和性格...")
        basic_layout.addWidget(self.prompt_input)

        # 用户偏好
        prefs_header = QHBoxLayout()
        prefs_title = QLabel("📋 用户偏好")
        prefs_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #333;")
        prefs_header.addWidget(prefs_title)
        prefs_header.addStretch()

        add_btn = QPushButton("+ 添加")
        add_btn.setFixedHeight(28)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FFD93D, stop:1 #FFC107);
                color: #333;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 500;
                padding: 0 12px;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FFC107, stop:1 #FF9800); }
        """)
        add_btn.clicked.connect(self._add_preference)
        prefs_header.addWidget(add_btn)

        del_btn = QPushButton("删除")
        del_btn.setFixedHeight(28)
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setStyleSheet("""
            QPushButton {
                background: #F5F5F5;
                color: #666;
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                font-size: 12px;
                padding: 0 12px;
            }
            QPushButton:hover { background: #FFEBEE; color: #FF6B6B; border-color: #FFCDD2; }
        """)
        del_btn.clicked.connect(self._del_preference)
        prefs_header.addWidget(del_btn)

        basic_layout.addLayout(prefs_header)

        # 列表高度自适应内容，最多显示5条，超出滚动
        self.prefs_list = QListWidget()
        self.prefs_list.setMaximumHeight(180)  # 约5条
        self.prefs_list.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.prefs_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        for p in self.config.get("persona", {}).get("user_preferences", []):
            self.prefs_list.addItem(p)
        # 根据条目数设置高度（最多5条高度）
        item_count = self.prefs_list.count()
        if item_count > 5:
            self.prefs_list.setFixedHeight(180)
        else:
            # 自适应高度
            self.prefs_list.setFixedHeight(max(36, 30 + item_count * 28))
        basic_layout.addWidget(self.prefs_list)

        tabs.addTab(basic_tab, "基础")

        # === 状态配置 ===
        state_tab = QWidget()
        state_layout = QVBoxLayout(state_tab)
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
        self.chat_size_small = QRadioButton("小 (400px)")
        self.chat_size_medium = QRadioButton("中 (480px)")
        self.chat_size_large = QRadioButton("大 (560px)")
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

        # 状态配置
        state_title = QLabel("🎨 状态配置")
        state_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #333; margin-top: 8px;")
        state_layout.addWidget(state_title)

        state_layout.addWidget(QLabel("选择状态:"))
        self.state_combo = QComboBox()
        self.state_combo.addItems(["idle (待机)", "click (点击)", "drag (拖拽)", "rest (休息)"])
        self.state_combo.currentIndexChanged.connect(self._load_state_config)
        state_layout.addWidget(self.state_combo)

        state_layout.addWidget(QLabel("动画文件:"))
        anim_layout = QHBoxLayout()
        self.anim_input = QLineEdit()
        self.anim_input.setPlaceholderText("GIF 文件路径 (留空使用默认)")
        anim_layout.addWidget(self.anim_input)
        browse_btn = QPushButton("浏览")
        browse_btn.setFixedWidth(60)
        browse_btn.setCursor(Qt.PointingHandCursor)
        browse_btn.setStyleSheet("""
            QPushButton {
                background: #F5F5F5;
                color: #666;
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                font-size: 12px;
            }
            QPushButton:hover { background: #EBEBEB; }
        """)
        browse_btn.clicked.connect(self._browse_animation)
        anim_layout.addWidget(browse_btn)
        state_layout.addLayout(anim_layout)

        state_layout.addWidget(QLabel("对话文本:"))
        self.state_dialog_input = QLineEdit()
        self.state_dialog_input.setPlaceholderText("该状态显示的对话")
        state_layout.addWidget(self.state_dialog_input)

        save_state_btn = QPushButton("💾 保存当前状态")
        save_state_btn.setFixedHeight(36)
        save_state_btn.setCursor(Qt.PointingHandCursor)
        save_state_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #E3F2FD, stop:1 #BBDEFB);
                color: #1976D2;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #BBDEFB, stop:1 #90CAF9); }
        """)
        save_state_btn.clicked.connect(self._save_state_config)
        state_layout.addWidget(save_state_btn)

        state_layout.addStretch()
        self._load_state_config(0)

        tabs.addTab(state_tab, "状态")
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

    def _add_preference(self):
        text, ok = QInputDialog.getText(self, "添加偏好", "输入用户偏好:")
        if ok and text.strip():
            self.prefs_list.addItem(text.strip())
            # 更新列表高度
            count = self.prefs_list.count()
            if count > 5:
                self.prefs_list.setFixedHeight(180)
            else:
                self.prefs_list.setFixedHeight(max(36, 30 + count * 28))

    def _del_preference(self):
        row = self.prefs_list.currentRow()
        if row >= 0:
            self.prefs_list.takeItem(row)
            # 更新列表高度
            count = self.prefs_list.count()
            if count > 5:
                self.prefs_list.setFixedHeight(180)
            elif count > 0:
                self.prefs_list.setFixedHeight(max(36, 30 + count * 28))
            else:
                self.prefs_list.setFixedHeight(36)

    def _load_state_config(self, index):
        states = ["idle", "click", "drag", "rest"]
        state_name = states[index]
        state_config = self.config.get("states", {}).get(state_name, {})

        anim = state_config.get("animation", "")
        if state_name == "idle":
            anims = state_config.get("animations", [])
            anim = "; ".join(anims) if anims else ""
        self.anim_input.setText(anim)

        dialog = state_config.get("dialog", "")
        if state_name == "idle":
            dialogs = state_config.get("dialogs", [])
            dialog = "; ".join(dialogs) if dialogs else ""
        self.state_dialog_input.setText(dialog)

    def _browse_animation(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择动画", "", "GIF Files (*.gif)")
        if file_path:
            self.anim_input.setText(file_path)

    def _save_state_config(self):
        states = ["idle", "click", "drag", "rest"]
        state_name = states[self.state_combo.currentIndex()]

        if "states" not in self.config:
            self.config["states"] = {}

        state_config = {}
        if state_name == "idle":
            anims = [a.strip() for a in self.anim_input.text().split(";") if a.strip()]
            dialogs = [d.strip() for d in self.state_dialog_input.text().split(";") if d.strip()]
            if anims: state_config["animations"] = anims
            if dialogs: state_config["dialogs"] = dialogs
        else:
            if self.anim_input.text().strip():
                state_config["animation"] = self.anim_input.text().strip()
            if self.state_dialog_input.text().strip():
                state_config["dialog"] = self.state_dialog_input.text().strip()

        self.config["states"][state_name] = state_config
        QMessageBox.information(self, "提示", f"{state_name} 已保存")

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
        self.config["persona"]["name"] = self.name_input.text().strip()
        self.config["persona"]["system_prompt"] = self.prompt_input.toPlainText()
        self.config["persona"]["user_preferences"] = [self.prefs_list.item(i).text() for i in range(self.prefs_list.count())]

        self.config.setdefault("ui", {})
        self.config["ui"]["pet_size"] = self.get_selected_size()
        self.config["ui"]["chat_window_size"] = self.get_chat_window_size()

        ConfigLoader.save(self.config)

        # API 配置变更提示重启
        if api_changed:
            QMessageBox.information(self, "提示", "API 配置已更新，重启应用后生效")

        self.accept()