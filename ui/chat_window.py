"""聊天窗口模块 - 精致圆角气泡对话框设计"""
from typing import TYPE_CHECKING

from PyQt5.QtCore import Qt, pyqtSignal, QThread, QTimer, QSize, QPointF
from PyQt5.QtGui import QPainter, QColor, QPainterPath, QFont, QFontMetrics, QPen, QBrush
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
)

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
    """圆角气泡控件 - 带阴影效果"""

    # 默认最大宽度，会在创建时被ChatWindow更新
    MAX_WIDTH = 300

    def __init__(self, text: str, is_user: bool = True, parent=None):
        super().__init__(parent)
        self.text = text
        self.is_user = is_user
        self._hover = False
        self._calculate_size()

    def _calculate_size(self):
        """计算气泡大小"""
        font = QFont("Microsoft YaHei UI", 12)
        fm = QFontMetrics(font)

        max_width = self.MAX_WIDTH
        text_rect = fm.boundingRect(0, 0, max_width, 0, Qt.TextWordWrap, self.text)

        self._text_width = min(text_rect.width() + 36, max_width)
        self._text_height = max(text_rect.height() + 28, 44)

        self.setFixedHeight(self._text_height + Spacing.LG + 4)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def paintEvent(self, event):
        """绘制圆角气泡"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        bubble_width = self._text_width
        bubble_height = self._text_height

        if self.is_user:
            x = self.width() - bubble_width - Spacing.XL
        else:
            x = Spacing.XL

        y = Spacing.SM
        radius = Radius.LG

        # 绘制阴影（仅 AI 气泡）
        if not self.is_user:
            shadow_path = QPainterPath()
            shadow_path.addRoundedRect(
                float(x + 1), float(y + 2),
                float(bubble_width), float(bubble_height),
                float(radius), float(radius)
            )
            painter.fillPath(shadow_path, Theme.SHADOW_LIGHT)

        # 绘制气泡主体
        path = QPainterPath()
        path.addRoundedRect(float(x), float(y), float(bubble_width), float(bubble_height), float(radius), float(radius))

        if self.is_user:
            painter.fillPath(path, QColor(Theme.BUBBLE_USER))
        else:
            painter.fillPath(path, QColor(Theme.BUBBLE_AI))
            painter.setPen(QPen(QColor(Theme.BORDER), 1))
            painter.drawPath(path)

        # 绘制文字
        painter.setPen(QColor(Theme.TEXT_ON_PRIMARY if self.is_user else Theme.TEXT_PRIMARY))
        font = QFont("Microsoft YaHei UI", 12)
        painter.setFont(font)

        text_rect = path.boundingRect().adjusted(18, 14, -18, -14)
        painter.drawText(text_rect, Qt.TextWordWrap, self.text)


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

        # 绘制图标
        font_icon = QFont("Segoe UI Emoji", 16)
        painter.setFont(font_icon)
        painter.setPen(QColor(Theme.PRIMARY))
        fm_icon = QFontMetrics(font_icon)
        icon_text = "⚡"
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
            self.finished.emit(full_response)
        except Exception as e:
            self.error.emit(str(e))


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

    def __init__(self, config, chat_service, memory_manager, persona_manager, parent=None):
        super().__init__(parent)
        self.config = config
        self.chat_service = chat_service
        self.memory_manager = memory_manager
        self.persona_manager = persona_manager

        size_key = config.get("ui", {}).get("chat_window_size", "medium")
        self.window_width, self.window_height = self.SIZE_MAP.get(size_key, (480, 600))

        # 设置气泡最大宽度为窗口宽度的40%
        BubbleWidget.MAX_WIDTH = int(self.window_width * 0.4)

        self.setWindowTitle(f"{persona_manager.name}")
        self.setFixedSize(self.window_width, self.window_height)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self._drag_pos = None
        self._worker = None
        self._pet_name = persona_manager.name
        self._streaming_bubble = None

        self._init_ui()

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
        self.container.setGraphicsEffect(shadow)

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

        # 标题
        self.title_label = QLabel(f"⚡ {self._pet_name}", title_bar)
        self.title_label.setGeometry(Spacing.LG, 0, w - 220, 56)
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
        self.scroll_area.setGeometry(0, 56, w, h - 118)
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
        input_bar = QWidget(self.container)
        input_bar.setGeometry(0, h - 62, w, 62)
        input_bar.setStyleSheet(f"""
            QWidget {{
                background: {Theme.BG_MAIN};
                border-top: 1px solid {Theme.DIVIDER};
                border-bottom-left-radius: {Radius.XXL}px;
                border-bottom-right-radius: {Radius.XXL}px;
            }}
        """)

        # 输入框
        self.message_input = QLineEdit(input_bar)
        self.message_input.setGeometry(Spacing.LG, 10, w - 180, 44)
        self.message_input.setPlaceholderText("输入消息...")
        self.message_input.setStyleSheet(f"""
            QLineEdit {{
                background: {Theme.BG_MAIN};
                border: 1px solid {Theme.BORDER};
                border-radius: 22px;
                padding: 0 {Spacing.LG}px;
                font-family: 'Microsoft YaHei UI', sans-serif;
                font-size: 16px;
                color: {Theme.TEXT_PRIMARY};
            }}
            QLineEdit:focus {{
                border: 2px solid {Theme.PRIMARY};
                padding: 0 15px;
            }}
            QLineEdit::placeholder {{
                color: {Theme.TEXT_PLACEHOLDER};
                font-size: 15px;
            }}
        """)
        self.message_input.returnPressed.connect(self._send_message)

        # 发送按钮
        self.send_btn = QPushButton("发送", input_bar)
        self.send_btn.setGeometry(w - 80, 10, 64, 44)
        self.send_btn.setCursor(Qt.PointingHandCursor)
        self.send_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.PRIMARY};
                color: {Theme.TEXT_ON_PRIMARY};
                border: none;
                border-radius: 22px;
                font-family: 'Microsoft YaHei UI', sans-serif;
                font-size: 15px;
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
        clear_btn = QPushButton("清空", input_bar)
        clear_btn.setGeometry(w - 150, 10, 64, 44)
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BG_INPUT};
                color: {Theme.TEXT_SECONDARY};
                border: none;
                border-radius: 22px;
                font-family: 'Microsoft YaHei UI', sans-serif;
                font-size: 15px;
            }}
            QPushButton:hover {{
                background-color: {Theme.ERROR_LIGHT};
                color: {Theme.ERROR};
            }}
        """)
        clear_btn.clicked.connect(self._clear_chat)

        # 状态提示
        self.status_label = QLabel("", self.container)
        self.status_label.setGeometry(Spacing.LG, h - 84, w - Spacing.XXL, 20)
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
        self.title_label.setText(f"⚡ {new_name}")
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
        text = self.message_input.text().strip()
        if not text or self._worker:
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
            self.message_layout.insertWidget(self.message_layout.count() - 1, self._streaming_bubble)

        self._streaming_bubble.text += chunk
        self._streaming_bubble._calculate_size()
        self._streaming_bubble.update()
        self._scroll_to_bottom()

    def _on_response(self, response):
        """响应完成"""
        if self._streaming_bubble:
            self._streaming_bubble.text = response
            self._streaming_bubble._calculate_size()
            self._streaming_bubble.update()

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
        self.message_layout.insertWidget(self.message_layout.count() - 1, bubble)
        if scroll:
            QTimer.singleShot(10, self._scroll_to_bottom)

    def _append_assistant_message(self, text, scroll=True):
        """添加 AI 消息"""
        bubble = BubbleWidget(text, is_user=False)
        self.message_layout.insertWidget(self.message_layout.count() - 1, bubble)
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