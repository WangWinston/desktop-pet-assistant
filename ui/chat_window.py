"""聊天窗口模块 - 精致圆角气泡对话框设计"""
import os
from typing import TYPE_CHECKING

from PyQt5.QtCore import Qt, pyqtSignal, QThread, QTimer, QSize, QPointF, QTime
from PyQt5.QtGui import (
    QPainter,
    QColor,
    QPainterPath,
    QFont,
    QFontMetrics,
    QPen,
    QBrush,
    QTextOption,
    QIcon,
    QPixmap,
)
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QSizePolicy,
    QGraphicsDropShadowEffect,
    QTextBrowser,
    QListWidget,
    QListWidgetItem,
    QDialog,
    QTimeEdit,
    QMessageBox,
)

from utils.todo_storage import TodoStorage
import markdown

if TYPE_CHECKING:
    from core.chat import ChatService
    from core.memory import MemoryManager
    from core.persona import PersonaManager


# ═══════════════════════════════════════════════════════════════════
# 设计系统 - 颜色与间距常量
# ═══════════════════════════════════════════════════════════════════
class Theme:
    """主题色板 - 温暖柔和的蓝灰色系"""
    # 主色调
    PRIMARY = "#5B8DEF"          # 主色 - 柔和蓝
    PRIMARY_HOVER = "#4A7FE0"    # 主色悬停
    PRIMARY_LIGHT = "#EBF2FF"    # 主色浅底

    # 背景色
    BG_MAIN = "#FFFFFF"          # 主背景
    BG_CHAT = "#F8FAFC"          # 聊天区背景
    BG_INPUT = "#F1F5F9"         # 输入框背景

    # 文字色
    TEXT_PRIMARY = "#1E293B"     # 主文字
    TEXT_SECONDARY = "#64748B"   # 次要文字
    TEXT_PLACEHOLDER = "#94A3B8" # 占位符
    TEXT_ON_PRIMARY = "#FFFFFF"  # 主色上的文字

    # 边框与分割
    BORDER = "#E2E8F0"           # 边框
    DIVIDER = "#F1F5F9"          # 分割线

    # 功能色
    SUCCESS = "#10B981"
    WARNING = "#F59E0B"
    ERROR = "#EF4444"
    ERROR_LIGHT = "#FEF2F2"
    ERROR_BORDER = "#FECACA"

    # 气泡色
    BUBBLE_USER = "#5B8DEF"
    BUBBLE_AI = "#FFFFFF"
    BUBBLE_SYSTEM = "#E2E8F0"

    # 阴影
    SHADOW_LIGHT = QColor(0, 0, 0, 8)
    SHADOW_MEDIUM = QColor(0, 0, 0, 12)


class Spacing:
    """间距常量"""
    XS = 4
    SM = 8
    MD = 12
    LG = 16
    XL = 24
    XXL = 32


class Radius:
    """圆角常量"""
    SM = 8
    MD = 12
    LG = 16
    XL = 20
    XXL = 24


class BubbleWidget(QWidget):
    """圆角气泡控件 - 支持Markdown渲染"""

    # 默认最大宽度，会在创建时被ChatWindow更新
    MAX_WIDTH = 300

    def __init__(self, text: str, is_user: bool = True, parent=None):
        super().__init__(parent)
        self.text = text
        self.is_user = is_user
        self._bg_color = Theme.BUBBLE_USER if is_user else Theme.BUBBLE_AI
        self._text_color = Theme.TEXT_ON_PRIMARY if is_user else Theme.TEXT_PRIMARY
        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        # 设置属性支持圆角
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(0)

        # 使用QTextBrowser支持Markdown
        self.text_browser = QTextBrowser()
        self.text_browser.setOpenExternalLinks(True)
        self.text_browser.setFrameShape(QTextBrowser.NoFrame)
        self.text_browser.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_browser.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_browser.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.text_browser.setOpenLinks(False)

        # 文本换行策略：即使是长单词/URL 也在气泡宽度内换行，避免水平溢出
        doc = self.text_browser.document()
        option = doc.defaultTextOption()
        option.setWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        doc.setDefaultTextOption(option)
        # 设置文档边距为0，避免额外留白
        doc.setDocumentMargin(0)

        self.text_browser.setStyleSheet(
            f"""
            QTextBrowser {{
                background-color: transparent;
                color: {self._text_color};
                border: none;
                font-family: 'Microsoft YaHei UI', sans-serif;
                font-size: 16px;
                line-height: 1.5;
            }}
            /* 段落与标题 - 减少边距避免留白 */
            p {{
                margin: 2px 0;
            }}
            h1, h2, h3 {{
                font-weight: 600;
                margin: 4px 0 2px 0;
            }}
            h1 {{
                font-size: 20px;
            }}
            h2 {{
                font-size: 18px;
            }}
            h3 {{
                font-size: 17px;
            }}
            /* Markdown 代码块样式 */
            pre {{
                background-color: {'#4A7FE0' if self.is_user else '#F0F0F0'};
                color: {self._text_color};
                padding: 8px;
                border-radius: 6px;
                margin: 4px 0;
            }}
            code {{
                background-color: {'#4A7FE0' if self.is_user else '#E8E8E8'};
                padding: 2px 6px;
                border-radius: 4px;
            }}
            /* 列表样式 */
            ul, ol {{
                margin-left: 20px;
                padding-left: 4px;
            }}
            li {{
                margin: 2px 0;
            }}
            /* 强调与引用 */
            strong {{
                font-weight: 600;
            }}
            em {{
                font-style: italic;
            }}
            blockquote {{
                border-left: 3px solid {Theme.BORDER};
                padding-left: 8px;
                margin: 6px 0;
                color: {Theme.TEXT_SECONDARY};
            }}
        """
        )

        # 设置Markdown内容
        self._update_text()
        layout.addWidget(self.text_browser)

    def paintEvent(self, event):
        """绘制圆角背景"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # AI气泡绘制阴影
        if not self.is_user:
            shadow_path = QPainterPath()
            shadow_path.addRoundedRect(1, 2, self.width() - 1, self.height() - 1, float(Radius.LG), float(Radius.LG))
            painter.fillPath(shadow_path, QColor(0, 0, 0, 15))

        # 绘制圆角矩形背景
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), float(Radius.LG), float(Radius.LG))
        painter.fillPath(path, QColor(self._bg_color))

        # AI气泡添加边框
        if not self.is_user:
            painter.setPen(QPen(QColor(Theme.BORDER), 1))
            painter.drawPath(path)

    def _update_text(self):
        """更新文本内容"""
        max_content_width = max(0, self.MAX_WIDTH - 28)  # 减去左右内边距

        # 使用样式表中定义的字体，确保宽度计算准确
        font = QFont('Microsoft YaHei UI', 16)

        if self.is_user:
            self.text_browser.setPlainText(self.text)
        else:
            # 使用 markdown 库转换为 HTML，支持完整 Markdown 功能
            html = markdown.markdown(
                self.text,
                extensions=['tables', 'fenced_code', 'toc', 'nl2br']
            )
            self.text_browser.setHtml(html)

        # 将字体应用到text_browser
        self.text_browser.setFont(font)
        font_metrics = QFontMetrics(font)

        # 计算每行文本的宽度，取最大值
        lines = self.text.split('\n')
        max_line_width = 0
        for line in lines:
            line_width = font_metrics.horizontalAdvance(line)
            max_line_width = max(max_line_width, line_width)

        # 实际宽度 = 文本宽度 + 紧凑边距
        # 用户消息：紧凑显示；AI消息：给代码块等留更多空间
        extra_padding = 24 if self.is_user else 32
        text_width = max_line_width + extra_padding
        actual_content_width = min(text_width, max_content_width)
        actual_content_width = max(actual_content_width, 30)  # 最小宽度

        # 设置文档宽度并计算高度
        doc = self.text_browser.document()
        doc.setTextWidth(actual_content_width)

        # 计算文档高度
        height = doc.size().height()

        # 根据内容类型调整高度
        # 纯文本高度较紧凑，Markdown内容需要更多空间
        min_height = 20
        self.text_browser.setFixedWidth(int(actual_content_width))
        self.text_browser.setFixedHeight(int(max(height, min_height)))

        # 气泡整体尺寸 = 内容尺寸 + 内边距
        # 布局 margins: left=14, top=10, right=14, bottom=10
        self.setFixedWidth(int(actual_content_width + 28))
        self.setFixedHeight(int(max(height, min_height) + 20))

    def set_text(self, text: str):
        """设置文本"""
        self.text = text
        self._update_text()

    def append_text(self, chunk: str):
        """追加文本（流式输出）"""
        self.text += chunk
        self._update_text()


class WelcomeWidget(QWidget):
    """欢迎消息控件"""

    def __init__(self, pet_name: str, parent=None):
        super().__init__(parent)
        self.pet_name = pet_name
        self.setFixedHeight(180)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        w = self.width()

        # ===== 图标区域 =====
        icon_center_y = 45
        icon_bg_radius = 30

        # 绘制图标背景圆
        icon_bg_path = QPainterPath()
        icon_bg_path.addEllipse(QPointF(w / 2, icon_center_y), icon_bg_radius, icon_bg_radius)
        painter.fillPath(icon_bg_path, QColor(Theme.PRIMARY_LIGHT))

        # 绘制图标（使用 icon.png）
        icon_path = "assets/icon.png"
        if os.path.exists(icon_path):
            icon_pixmap = QPixmap(icon_path)
            if not icon_pixmap.isNull():
                icon_size = 40
                scaled_pixmap = icon_pixmap.scaled(icon_size, icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                icon_x = int(w / 2 - icon_size / 2)
                icon_y = int(icon_center_y - icon_size / 2)
                painter.drawPixmap(icon_x, icon_y, scaled_pixmap)
        else:
            # 回退到文字图标
            font_icon = QFont("Segoe UI Emoji", 16)
            painter.setFont(font_icon)
            painter.setPen(QColor(Theme.PRIMARY))
            fm_icon = QFontMetrics(font_icon)
            icon_text = "🐾"
            icon_x = int(w / 2 - fm_icon.horizontalAdvance(icon_text) / 2)
            icon_y = int(icon_center_y + fm_icon.ascent() / 2 - 2)
            painter.drawText(icon_x, icon_y, icon_text)

        # ===== 标题 =====
        font_title = QFont("Microsoft YaHei UI", 14, QFont.Medium)
        painter.setFont(font_title)
        painter.setPen(QColor(Theme.TEXT_PRIMARY))
        fm_title = QFontMetrics(font_title)
        title_text = f"你好，我是 {self.pet_name}"
        title_x = int(w / 2 - fm_title.horizontalAdvance(title_text) / 2)
        title_y = icon_center_y + icon_bg_radius + 30
        painter.drawText(title_x, title_y, title_text)

        # ===== 副标题 =====
        font_sub = QFont("Microsoft YaHei UI", 10)
        painter.setFont(font_sub)
        painter.setPen(QColor(Theme.TEXT_SECONDARY))
        fm_sub = QFontMetrics(font_sub)
        sub_text = "有什么想聊的吗？"
        sub_x = int(w / 2 - fm_sub.horizontalAdvance(sub_text) / 2)
        sub_y = title_y + 30
        painter.drawText(sub_x, sub_y, sub_text)


class SystemMessageWidget(QWidget):
    """系统消息控件"""

    def __init__(self, text: str, is_error: bool = False, parent=None):
        super().__init__(parent)
        self.text = text
        self.is_error = is_error
        self.setFixedHeight(36)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        font = QFont("Microsoft YaHei UI", 9)
        fm = QFontMetrics(font)
        text_width = fm.horizontalAdvance(self.text) + 28
        text_height = 26

        x = (self.width() - text_width) // 2
        y = 5
        radius = Radius.SM

        path = QPainterPath()
        path.addRoundedRect(float(x), float(y), float(text_width), float(text_height), float(radius), float(radius))

        if self.is_error:
            painter.fillPath(path, QColor(Theme.ERROR_LIGHT))
            painter.setPen(QPen(QColor(Theme.ERROR_BORDER), 1))
            painter.drawPath(path)
            text_color = Theme.ERROR
        else:
            painter.fillPath(path, QColor(Theme.BUBBLE_SYSTEM))
            text_color = Theme.TEXT_SECONDARY

        painter.setFont(font)
        painter.setPen(QColor(text_color))
        painter.drawText(path.boundingRect(), Qt.AlignCenter, self.text)


class TodoDialog(QDialog):
    """添加待办事项弹窗"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._content = ""
        self._time_str = ""
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("添加待办事项")
        # 仅保留关闭按钮，去掉帮助按钮
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setModal(True)
        self.setMinimumWidth(360)
        self.setMinimumHeight(200)

        # 设置窗口图标
        icon_path = "assets/icon.png"
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # 应用与项目一致的主题样式
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Theme.BG_MAIN};
                border-radius: 16px;
            }}
            QLabel {{
                font-family: 'Microsoft YaHei UI', sans-serif;
                background: transparent;
            }}
            QLineEdit {{
                padding: 12px 16px;
                border: 1px solid {Theme.BORDER};
                border-radius: 10px;
                background: {Theme.BG_CHAT};
                font-family: 'Microsoft YaHei UI', sans-serif;
                font-size: 14px;
                color: {Theme.TEXT_PRIMARY};
            }}
            QLineEdit:focus {{
                border: 2px solid {Theme.PRIMARY};
                padding: 11px 15px;
            }}
            QLineEdit::placeholder {{
                color: {Theme.TEXT_PLACEHOLDER};
            }}
            QTimeEdit {{
                padding: 12px 16px;
                border: 1px solid {Theme.BORDER};
                border-radius: 10px;
                background: {Theme.BG_CHAT};
                font-family: 'Microsoft YaHei UI', sans-serif;
                font-size: 14px;
                color: {Theme.TEXT_PRIMARY};
                min-height: 20px;
            }}
            QTimeEdit:focus {{
                border: 2px solid {Theme.PRIMARY};
            }}
            QTimeEdit::drop-down {{
                border: none;
                width: 0px;
                subcontrol-position: right center;
            }}
            QTimeEdit::down-arrow {{
                image: none;
                width: 0px;
            }}
            QTimeEdit::up-button {{
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 0px;
                border: none;
                background: transparent;
            }}
            QTimeEdit::down-button {{
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 0px;
                border: none;
                background: transparent;
            }}
            QTimeEdit QSpinBox {{
                background: transparent;
                border: none;
            }}
            QPushButton {{
                padding: 12px 24px;
                border: none;
                border-radius: 10px;
                font-family: 'Microsoft YaHei UI', sans-serif;
                font-size: 14px;
                font-weight: 500;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(16)

        # 标题
        title_label = QLabel("新增待办")
        title_label.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 600;
            color: {Theme.TEXT_PRIMARY};
        """)
        layout.addWidget(title_label)

        # 内容输入
        self.content_input = QLineEdit()
        self.content_input.setPlaceholderText("请输入待办内容")
        layout.addWidget(self.content_input)

        # 时间选择行
        time_row = QWidget()
        time_layout = QHBoxLayout(time_row)
        time_layout.setContentsMargins(0, 0, 0, 0)
        time_layout.setSpacing(12)

        time_label = QLabel("提醒时间")
        time_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 13px;")
        time_label.setFixedWidth(70)
        time_layout.addWidget(time_label)

        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        # 默认设为下一个整点
        from datetime import datetime, timedelta
        current = datetime.now()
        next_hour = (current + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        default_time = QTime.fromString(next_hour.strftime("%H:%M"), "HH:mm")
        if default_time.isValid():
            self.time_edit.setTime(default_time)
        time_layout.addWidget(self.time_edit)
        time_layout.addStretch()

        layout.addWidget(time_row)

        # 按钮行
        btn_row = QWidget()
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.setContentsMargins(0, 8, 0, 0)
        btn_layout.setSpacing(12)

        cancel_btn = QPushButton("取消")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.BG_INPUT};
                color: {Theme.TEXT_SECONDARY};
            }}
            QPushButton:hover {{
                background: {Theme.BORDER};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("保存")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.PRIMARY};
                color: {Theme.TEXT_ON_PRIMARY};
            }}
            QPushButton:hover {{
                background: {Theme.PRIMARY_HOVER};
            }}
        """)
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(save_btn)

        layout.addWidget(btn_row)

    def _on_save(self):
        content = self.content_input.text().strip()
        if not content:
            QMessageBox.warning(self, "提示", "请输入待办内容")
            return

        time_str = self.time_edit.time().toString("HH:mm")
        if not time_str:
            QMessageBox.warning(self, "提示", "请选择提醒时间")
            return

        self._content = content
        self._time_str = time_str
        self.accept()

    def get_todo(self):
        return self._content, self._time_str


class ChatWorker(QThread):
    """后台聊天线程 - 流式输出"""
    chunk_received = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, chat_service, messages):
        super().__init__()
        self.chat_service = chat_service
        self.messages = messages

    def run(self):
        try:
            full_response = ""
            for chunk in self.chat_service.chat_stream(self.messages):
                full_response += chunk
                self.chunk_received.emit(chunk)
            # 最终清理：移除可能残留的工具调用标记
            full_response = self._clean_tool_markers(full_response)
            self.finished.emit(full_response)
        except Exception as e:
            self.error.emit(str(e))
    
    def _clean_tool_markers(self, content: str) -> str:
        """清理模型输出的工具调用标记"""
        import re
        # 移除 minimax:tool_call ... /minimax:tool_call 标记及其内容
        content = re.sub(r'minimax:tool_call\s*.*?/minimax:tool_call', '', content, flags=re.DOTALL)
        # 移除残留的单独标记
        content = re.sub(r'minimax:tool_call\s*', '', content)
        content = re.sub(r'/minimax:tool_call\s*', '', content)
        # 移除其他工具调用标记
        content = re.sub(r'<antml:function_calls>.*?</antml:function_calls>', '', content, flags=re.DOTALL)
        content = re.sub(r'<function_calls>.*?</function_calls>', '', content, flags=re.DOTALL)
        # 清理多余空白
        content = re.sub(r'\n{3,}', '\n\n', content)
        return content.strip()


class ProfileAnalyzeWorker(QThread):
    """后台分析用户画像线程"""
    finished = pyqtSignal(dict)

    def __init__(self, persona_manager, messages, api_config):
        super().__init__()
        self.persona_manager = persona_manager
        self.messages = messages
        self.api_config = api_config

    def run(self):
        try:
            profile = self.persona_manager.analyze_user_profile(self.messages, self.api_config)
            self.finished.emit(profile)
        except:
            self.finished.emit({})


class ChatWindow(QWidget):
    """聊天窗口 - 精致圆角气泡对话框设计"""

    SIZE_MAP = {
        "small": (520, 620),
        "medium": (660, 740),
        "large": (1200, 880),
    }

    settings_requested = pyqtSignal()

    def __init__(self, config, chat_service, memory_manager, persona_manager, parent=None, pet=None):
        super().__init__(parent)
        self.config = config
        self.chat_service = chat_service
        self.memory_manager = memory_manager
        self.persona_manager = persona_manager
        self._pet = pet  # 保存 pet 引用

        size_key = config.get("ui", {}).get("chat_window_size", "medium")
        self.window_width, self.window_height = self.SIZE_MAP.get(
            size_key, self.SIZE_MAP["medium"]
        )

        # 不同窗口尺寸下的气泡宽度占比，尽量减少多余留白
        bubble_width_ratio_map = {
            "small": 0.8,
            "medium": 0.7,
            "large": 0.6,
        }
        bubble_ratio = bubble_width_ratio_map.get(size_key, 0.7)
        BubbleWidget.MAX_WIDTH = int(self.window_width * bubble_ratio)

        self.setWindowTitle(f"{persona_manager.name}")
        self.setFixedSize(self.window_width, self.window_height)
        # 使用无边框置顶窗口，但不再启用整窗透明，以提升性能和稳定性
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        # 设置窗口图标
        icon_path = "assets/icon.png"
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self._drag_pos = None
        self._worker = None
        self._pet_name = persona_manager.name
        self._streaming_bubble = None
        self._streaming_container = None
        self._skills_popup = None

        self._init_ui()

    # ═══════════════════════════════════════════════════════
    # 斜杠技能选择相关
    # ═══════════════════════════════════════════════════════

    def _ensure_skills_popup(self):
        """延迟创建技能列表弹窗"""
        if self._skills_popup is not None:
            return

        self._skills_popup = QListWidget(self.container)
        self._skills_popup.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self._skills_popup.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._skills_popup.setFocusPolicy(Qt.NoFocus)
        self._skills_popup.setStyleSheet(
            f"""
            QListWidget {{
                background: {Theme.BG_MAIN};
                border: 1px solid {Theme.BORDER};
                border-radius: {Radius.MD}px;
                font-family: 'Microsoft YaHei UI', sans-serif;
                font-size: 13px;
                color: {Theme.TEXT_PRIMARY};
            }}
            QListWidget::item {{
                padding: 6px 10px;
            }}
            QListWidget::item:selected {{
                background: {Theme.PRIMARY_LIGHT};
                color: {Theme.PRIMARY};
            }}
        """
        )
        self._skills_popup.hide()
        self._skills_popup.itemClicked.connect(self._on_skill_item_activated)
        self._skills_popup.itemActivated.connect(self._on_skill_item_activated)

    def _hide_skills_popup(self):
        if self._skills_popup is not None:
            self._skills_popup.hide()

    def _on_input_changed(self, text: str):
        """输入内容变化时，根据 / 前缀显示技能列表"""
        if not text.startswith("/"):
            self._hide_skills_popup()
            return

        # 优先使用 PersonaManager 已加载的技能
        skills = self.persona_manager.get_skills()
        # 兜底：如果还没有加载到技能，则直接从配置的 skills 目录重新加载一次
        if not skills:
            try:
                from core.persona import load_skills

                skills_dir = self.config.get("skills", {}).get("directory", "skills")
                skills = load_skills(skills_dir)
            except Exception:
                skills = {}

        if not skills:
            self._hide_skills_popup()
            return

        # 添加内置命令到技能列表顶部
        builtin_commands = {
            "todo": {
                "name": "todo",
                "description": "创建待办提醒,格式：内容@时间，例如：开会@10:00"
            }
        }
        # 合并内置命令（内置命令优先）
        skills = {**builtin_commands, **skills}

        query = text[1:].strip().lower()

        # 筛选技能
        matched_items = []
        for skill_key, skill_info in skills.items():
            display_name = skill_info.get("name") or skill_key
            desc = skill_info.get("description", "")
            label = f"{display_name} - {desc}" if desc else display_name

            if query:
                haystack = f"{display_name} {desc}".lower()
                if query not in haystack:
                    continue

            matched_items.append((display_name, label))

        if not matched_items:
            self._hide_skills_popup()
            return

        self._ensure_skills_popup()
        self._skills_popup.clear()

        for display_name, label in matched_items:
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, display_name)
            self._skills_popup.addItem(item)

        # 计算弹窗位置：对齐输入框上方
        bar_geo = self.input_bar.geometry()
        input_geo = self.message_input.geometry()

        popup_width = input_geo.width()
        popup_height = min(180, 30 + 26 * len(matched_items))

        x = bar_geo.x() + input_geo.x()
        y = bar_geo.y() - popup_height - 6
        if y < 0:
            y = 0

        self._skills_popup.setGeometry(x, y, popup_width, popup_height)
        self._skills_popup.show()
        self._skills_popup.raise_()

    def _on_skill_item_activated(self, item: QListWidgetItem):
        """选择某个技能后，将其填充到输入框中"""
        if not item:
            return
        skill_name = item.data(Qt.UserRole) or item.text()
        self.message_input.setText(f"/{skill_name} ")
        self.message_input.setFocus()
        self.message_input.setCursorPosition(len(self.message_input.text()))
        self._hide_skills_popup()

    def _init_ui(self):
        """初始化 UI"""
        w, h = self.window_width, self.window_height

        # 主容器 - 带阴影的圆角白色背景
        self.container = QWidget(self)
        self.container.setGeometry(0, 0, w, h)
        self.container.setStyleSheet(f"""
            QWidget#container {{
                background: {Theme.BG_MAIN};
                border-radius: {Radius.XXL}px;
            }}
        """)
        self.container.setObjectName("container")

        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 4)
        # 关闭窗口阴影以减少重绘压力
        # self.container.setGraphicsEffect(shadow)

        # ═══════════════════════════════════════════════════════
        # 顶部标题栏
        # ═══════════════════════════════════════════════════════
        title_bar = QWidget(self.container)
        title_bar.setGeometry(0, 0, w, 56)
        title_bar.setStyleSheet(f"""
            QWidget {{
                background: {Theme.BG_MAIN};
                border-top-left-radius: {Radius.XXL}px;
                border-top-right-radius: {Radius.XXL}px;
                border-bottom: 1px solid {Theme.DIVIDER};
            }}
        """)

        # 标题图标
        self.title_icon = QLabel(title_bar)
        self.title_icon.setGeometry(Spacing.LG, 14, 28, 28)
        icon_path = "assets/icon.png"
        if os.path.exists(icon_path):
            icon_pixmap = QPixmap(icon_path)
            if not icon_pixmap.isNull():
                self.title_icon.setPixmap(icon_pixmap.scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.title_icon.setStyleSheet("background: transparent;")

        # 标题
        self.title_label = QLabel(self._pet_name, title_bar)
        self.title_label.setGeometry(Spacing.LG + 32, 0, w - 250, 56)
        self.title_label.setStyleSheet(f"""
            QLabel {{
                font-family: 'Microsoft YaHei UI', sans-serif;
                font-size: 16px;
                font-weight: 600;
                color: {Theme.TEXT_PRIMARY};
                background: transparent;
            }}
        """)

        # 设置按钮
        self.settings_btn = QPushButton("⚙", title_bar)
        self.settings_btn.setGeometry(w - 108, 13, 36, 30)
        self.settings_btn.setCursor(Qt.PointingHandCursor)
        self.settings_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Theme.TEXT_SECONDARY};
                border: none;
                border-radius: {Radius.SM}px;
                font-size: 16px;
            }}
            QPushButton:hover {{
                background: {Theme.BG_INPUT};
                color: {Theme.TEXT_PRIMARY};
            }}
        """)
        self.settings_btn.clicked.connect(self.settings_requested.emit)

        # 关闭按钮
        close_btn = QPushButton("✕", title_bar)
        close_btn.setGeometry(w - 66, 13, 36, 30)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Theme.TEXT_SECONDARY};
                border: none;
                border-radius: {Radius.SM}px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background: {Theme.ERROR};
                color: {Theme.TEXT_ON_PRIMARY};
            }}
        """)
        close_btn.clicked.connect(self.hide)

        # ═══════════════════════════════════════════════════════
        # 中间对话区域
        # ═══════════════════════════════════════════════════════
        self.scroll_area = QScrollArea(self.container)
        header_height = 56
        input_height = 72
        self.scroll_area.setGeometry(0, header_height, w, h - header_height - input_height)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: {Theme.BG_CHAT};
                border: none;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 6px;
                margin: 8px 2px;
            }}
            QScrollBar::handle:vertical {{
                background: {Theme.BORDER};
                border-radius: 3px;
                min-height: 40px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {Theme.TEXT_PLACEHOLDER};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)

        # 消息容器
        self.message_container = QWidget()
        self.message_container.setStyleSheet(f"background: {Theme.BG_CHAT};")
        self.message_layout = QVBoxLayout(self.message_container)
        self.message_layout.setContentsMargins(Spacing.SM, Spacing.MD, Spacing.SM, Spacing.MD)
        self.message_layout.setSpacing(Spacing.XS)
        self.message_layout.addStretch()

        self.scroll_area.setWidget(self.message_container)

        # 欢迎消息
        self._append_welcome()

        # 加载历史
        self._load_history()

        # ═══════════════════════════════════════════════════════
        # 底部输入栏
        # ═══════════════════════════════════════════════════════
        self.input_bar = QWidget(self.container)
        self.input_bar.setGeometry(0, h - input_height, w, input_height)
        self.input_bar.setStyleSheet(f"""
            QWidget {{
                background: {Theme.BG_MAIN};
                border-top: 1px solid {Theme.DIVIDER};
                border-bottom-left-radius: {Radius.XXL}px;
                border-bottom-right-radius: {Radius.XXL}px;
            }}
        """)

        # 输入框
        self.message_input = QLineEdit(self.input_bar)
        self.message_input.setGeometry(Spacing.LG, 12, w - 210, 48)
        self.message_input.setPlaceholderText("输入消息...")
        self.message_input.setStyleSheet(f"""
            QLineEdit {{
                background: {Theme.BG_MAIN};
                border: 1px solid {Theme.BORDER};
                border-radius: 24px;
                padding: 0 {Spacing.LG}px;
                font-family: 'Microsoft YaHei UI', sans-serif;
                font-size: 17px;
                color: {Theme.TEXT_PRIMARY};
            }}
            QLineEdit:focus {{
                border: 2px solid {Theme.PRIMARY};
                padding: 0 15px;
            }}
            QLineEdit::placeholder {{
                color: {Theme.TEXT_PLACEHOLDER};
                font-size: 16px;
            }}
        """)
        self.message_input.returnPressed.connect(self._send_message)

        # 发送按钮
        self.send_btn = QPushButton("发送", self.input_bar)
        self.send_btn.setGeometry(w - 92, 12, 80, 48)
        self.send_btn.setCursor(Qt.PointingHandCursor)
        self.send_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.PRIMARY};
                color: {Theme.TEXT_ON_PRIMARY};
                border: none;
                border-radius: 24px;
                font-family: 'Microsoft YaHei UI', sans-serif;
                font-size: 16px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {Theme.PRIMARY_HOVER};
            }}
            QPushButton:disabled {{
                background-color: {Theme.BORDER};
            }}
        """)
        self.send_btn.clicked.connect(self._send_message)

        # 清空对话按钮
        clear_btn = QPushButton("清空", self.input_bar)
        clear_btn.setGeometry(w - 186, 12, 80, 48)
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BG_INPUT};
                color: {Theme.TEXT_SECONDARY};
                border: none;
                border-radius: 24px;
                font-family: 'Microsoft YaHei UI', sans-serif;
                font-size: 16px;
            }}
            QPushButton:hover {{
                background-color: {Theme.ERROR_LIGHT};
                color: {Theme.ERROR};
            }}
        """)
        clear_btn.clicked.connect(self._clear_chat)

        # 输入变更时处理斜杠技能选择
        self.message_input.textChanged.connect(self._on_input_changed)

        # 状态提示
        self.status_label = QLabel("", self.container)
        self.status_label.setGeometry(Spacing.LG, h - input_height - 22, w - Spacing.XXL, 20)
        self.status_label.setStyleSheet(f"""
            color: {Theme.TEXT_SECONDARY};
            font-family: 'Microsoft YaHei UI', sans-serif;
            font-size: 12px;
            background: transparent;
        """)

    def _clear_chat(self):
        """清空对话"""
        # 后台分析用户画像
        messages = self.memory_manager.get_messages()
        if len(messages) >= 4:
            api_config = self.config.get("api", {})
            self._analyze_worker = ProfileAnalyzeWorker(self.persona_manager, messages, api_config)
            self._analyze_worker.finished.connect(self._on_analyze_done)
            self._analyze_worker.start()

        self.memory_manager.clear()
        while self.message_layout.count() > 1:
            item = self.message_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._append_welcome()
        self._append_system_message("对话已清空")

    def _on_analyze_done(self, profile: dict):
        """分析完成"""
        if profile:
            for dim_key, value in profile.items():
                if value:
                    self.persona_manager.update_user_profile(dim_key, value)
            from core.persona import DEFAULT_NAME
            self._append_system_message(f"已更新用户画像~{DEFAULT_NAME}更了解你了！")

    def update_persona_name(self, new_name):
        """更新人设名称"""
        self._pet_name = new_name
        self.setWindowTitle(new_name)
        self.title_label.setText(new_name)
        # 更新标题图标
        icon_path = "assets/icon.png"
        if os.path.exists(icon_path):
            icon_pixmap = QPixmap(icon_path)
            if not icon_pixmap.isNull():
                self.title_icon.setPixmap(icon_pixmap.scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        while self.message_layout.count() > 0:
            item = self.message_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.message_layout.addStretch()
        self._append_welcome()
        self._load_history()

    def _append_welcome(self):
        """欢迎消息"""
        welcome = WelcomeWidget(self._pet_name)
        self.message_layout.insertWidget(self.message_layout.count() - 1, welcome)

    def _load_history(self):
        """加载历史对话"""
        messages = self.memory_manager.get_messages()[-20:]
        for msg in messages:
            if msg["role"] == "user":
                self._append_user_message(msg["content"], scroll=False)
            elif msg["role"] == "assistant":
                self._append_assistant_message(msg["content"], scroll=False)

    def _send_message(self):
        """发送消息"""
        # 若技能选择弹窗还在，则先隐藏
        self._hide_skills_popup()

        text = self.message_input.text().strip()
        if not text or self._worker:
            return

        # 检查是否是 /todo 命令
        if text == "/todo":
            self.message_input.clear()
            self._open_todo_dialog()
            return
        if text.startswith("/todo "):
            self.message_input.clear()
            self._handle_todo_command(text[6:].strip())
            return

        self.message_input.clear()
        self._append_user_message(text)
        self.memory_manager.add_message("user", text)

        if self.memory_manager.should_compress():
            self.status_label.setText("整理记忆中...")
            self.memory_manager.compress()

        messages = [self.persona_manager.get_system_message()]
        messages.extend(self.memory_manager.get_messages())

        self.send_btn.setEnabled(False)
        self.status_label.setText("思考中...")

        self._worker = ChatWorker(self.chat_service, messages)
        self._worker.chunk_received.connect(self._on_chunk)
        self._worker.finished.connect(self._on_response)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_chunk(self, chunk):
        """流式接收"""
        if self._streaming_bubble is None:
            self._streaming_bubble = BubbleWidget("", is_user=False)
            # 左对齐容器
            self._streaming_container = QWidget()
            layout = QHBoxLayout(self._streaming_container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(self._streaming_bubble)
            layout.addStretch()
            self.message_layout.insertWidget(self.message_layout.count() - 1, self._streaming_container)

        self._streaming_bubble.append_text(chunk)
        self._scroll_to_bottom()

    def _on_response(self, response):
        """响应完成"""
        if self._streaming_bubble:
            self._streaming_bubble.set_text(response)

        self.memory_manager.add_message("assistant", response)
        self._finish_request()
        self._streaming_bubble = None

    def _on_error(self, error):
        """错误处理"""
        if self._streaming_bubble:
            self.message_layout.removeWidget(self._streaming_bubble)
            self._streaming_bubble.deleteLater()
            self._streaming_bubble = None
        self._append_error_message(f"发送失败: {error}")
        self._finish_request()

    def _finish_request(self):
        self._worker = None
        self.send_btn.setEnabled(True)
        self.status_label.setText("")

    def _append_user_message(self, text, scroll=True):
        """添加用户消息"""
        bubble = BubbleWidget(text, is_user=True)
        # 右对齐
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch()
        layout.addWidget(bubble)
        self.message_layout.insertWidget(self.message_layout.count() - 1, container)
        if scroll:
            QTimer.singleShot(10, self._scroll_to_bottom)

    def _open_todo_dialog(self):
        """打开新增待办弹窗"""
        dialog = TodoDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            content, time_str = dialog.get_todo()
            if content and time_str:
                self._save_todo(content, time_str)

    def _parse_todo_text(self, text: str):
        """解析 /todo 命令文本，返回 (content, time_str)"""
        import re
        from datetime import datetime, timedelta

        # 支持 "内容 @ 时间" 或 "内容@时间" 或 "内容 时间"
        match = re.match(r'^(.+?)\s*@\s*(\d{1,2}:\d{2})$', text)
        if match:
            content = match.group(1).strip()
            time_str = match.group(2).strip()
            return content, time_str

        match2 = re.match(r'^(.+?)\s+(\d{1,2}:\d{2})$', text)
        if match2:
            content = match2.group(1).strip()
            time_str = match2.group(2).strip()
            return content, time_str

        content = text.strip()
        if not content:
            return "", ""

        # 默认时间设为当前时间的下一个整点
        current = datetime.now()
        next_hour = (current + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        time_str = next_hour.strftime("%H:%M")
        return content, time_str

    def _handle_todo_command(self, text: str):
        """处理 /todo 文本命令"""
        try:
            content, time_str = self._parse_todo_text(text)
            if not content:
                self._append_assistant_message("❌ 请输入待办内容\n格式：/todo 开会@10:00 或 /todo 开会 @ 10:00")
                return

            self._save_todo(content, time_str)
        except Exception as e:
            import traceback

            error_msg = f"❌ 添加失败: {str(e)}\\n{traceback.format_exc()}"
            self._append_assistant_message(error_msg)

    def _save_todo(self, content: str, time_str: str):
        """保存待办到文件，并刷新宠物与设置窗口"""
        # 先加载当前列表以判断是否重复
        before = TodoStorage.load_todos()
        todos = TodoStorage.add_todo(content, time_str)
        if len(todos) == len(before):
            self._append_assistant_message(f"⚠️ 待办已存在: {content} @ {time_str}")
            return

        # 刷新宠物中的待办配置
        if hasattr(self, "_pet") and self._pet:
            if hasattr(self._pet, "refresh_todo_config"):
                self._pet.refresh_todo_config()

            # 如果宠物有打开的设置窗口，也刷新它
            if hasattr(self._pet, "_settings_dialog") and self._pet._settings_dialog:
                settings = self._pet._settings_dialog
                if hasattr(settings, "todo_list"):
                    settings.todo_list.clear()
                    for todo in todos:
                        t_content = todo.get("content", "")
                        t_time = todo.get("time", "")
                        done = todo.get("done", False)
                        item_text = f"[{'✓' if done else '○'}] {t_content} @ {t_time}"
                        settings.todo_list.addItem(item_text)

        self._append_assistant_message(f"✅ 待办已添加: {content}\n将在 {time_str} 提醒你")

    def _append_assistant_message(self, text, scroll=True):
        """添加 AI 消息"""
        bubble = BubbleWidget(text, is_user=False)
        # 左对齐
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(bubble)
        layout.addStretch()
        self.message_layout.insertWidget(self.message_layout.count() - 1, container)
        if scroll:
            QTimer.singleShot(10, self._scroll_to_bottom)

    def _append_system_message(self, text):
        """系统消息"""
        msg = SystemMessageWidget(text)
        self.message_layout.insertWidget(self.message_layout.count() - 1, msg)

    def _append_error_message(self, text):
        """错误消息"""
        msg = SystemMessageWidget(f"⚠ {text}", is_error=True)
        self.message_layout.insertWidget(self.message_layout.count() - 1, msg)

    def _scroll_to_bottom(self):
        """滚动到底部"""
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.pos()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_pos:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None