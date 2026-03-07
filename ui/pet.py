"""桌面宠物主窗口模块 - 支持自定义状态"""
import os
import random
import sys

from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QMovie, QCursor
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QLabel,
    QMenu,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from core.chat import ChatService
from core.compressor import Compressor
from core.memory import MemoryManager
from core.persona import PersonaManager
from ui.chat_window import ChatWindow
from ui.settings_dialog import SettingsDialog
from utils.config_loader import ConfigLoader

# 默认状态配置
DEFAULT_STATES = {
    "idle": {
        "animations": [],  # 空则使用默认目录
        "dialogs": []      # 空则使用默认文件
    },
    "click": {
        "animation": "assets/click/click.gif",
        "dialog": "⚡ 别戳我！",
        "style": "color: white; background-color: #FF8E53;"
    },
    "drag": {
        "animation": "",
        "dialog": "✋ 带我飞~",
        "style": "color: #333; background-color: #FFD93D;"
    },
    "rest": {
        "animation": "",
        "dialog": "⏰ 该休息啦！",
        "style": "color: white; background-color: #FF6B6B;"
    }
}


class SummaryWorker(QThread):
    """后台总结线程"""
    finished = pyqtSignal(str)

    def __init__(self, chat_service, messages):
        super().__init__()
        self.chat_service = chat_service
        self.messages = messages

    def run(self):
        try:
            prompt = """请分析以下对话，提取用户的重要特征、偏好、习惯等，以简洁的列表形式总结（每条不超过20字）：

""" + "\n".join([
    f"{'用户' if m['role']=='user' else '助手'}: {m['content'][:100]}"
    for m in self.messages[-30:]
    if m['role'] in ['user', 'assistant']
])
            response = self.chat_service.chat([{"role": "user", "content": prompt}])
            self.finished.emit(response)
        except:
            self.finished.emit("")


class DesktopPet(QWidget):
    """桌面宠物 - 支持自定义状态"""

    # 状态名称
    STATE_IDLE = "idle"
    STATE_CLICK = "click"
    STATE_DRAG = "drag"
    STATE_REST = "rest"

    def __init__(self, parent=None):
        super().__init__(parent)

        # 加载配置
        self.config = ConfigLoader.load()

        # 初始化核心模块
        self.chat_service = ChatService(self.config)
        self.compressor = Compressor(self.chat_service)
        self.memory_manager = MemoryManager(self.config, self.chat_service, self.compressor)
        self.memory_manager.load_from_file()
        self.persona_manager = PersonaManager(self.config)

        # 加载状态配置
        self._load_states_config()

        # 状态
        self._current_state = self.STATE_IDLE
        self._rest_enabled = False
        self._drag_pos = None
        self._chat_window = None
        self._pet_size = self.config.get("ui", {}).get("pet_size", 100)

        # 初始化窗口
        self._init_window()
        self._init_tray()
        self._init_pet()
        self._init_timers()

    def _load_states_config(self):
        """加载状态配置"""
        self.states = {}
        config_states = self.config.get("states", {})

        for state_name in [self.STATE_IDLE, self.STATE_CLICK, self.STATE_DRAG, self.STATE_REST]:
            if state_name in config_states:
                self.states[state_name] = config_states[state_name]
            else:
                self.states[state_name] = DEFAULT_STATES.get(state_name, {})

    def _init_window(self):
        """初始化窗口"""
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow
        )
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

    def _init_tray(self):
        """初始化系统托盘"""
        icon_path = "assets/tigerIcon.jpg"
        if not os.path.exists(icon_path):
            icon_path = "tigerIcon.jpg"

        icon = QIcon(icon_path)
        tray_menu = QMenu(self)

        show_action = QAction("显示", self, triggered=self._show_window)
        chat_action = QAction("聊天", self, triggered=self._open_chat)
        quit_action = QAction("退出", self, triggered=self._quit)

        tray_menu.addAction(show_action)
        tray_menu.addAction(chat_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)

        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(icon)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def _init_pet(self):
        """初始化宠物"""
        # 计算字体大小
        font_size = max(10, int(self._pet_size / 12))

        # 对话框标签
        self.talk_label = QLabel(self)
        self.talk_label.setStyleSheet(f"""
            QLabel {{
                font-family: 'Microsoft YaHei UI';
                font-size: {font_size}px;
                color: #333;
                background-color: white;
                border: 1px solid #FFD93D;
                border-radius: 10px;
                padding: 6px 10px;
            }}
        """)
        self.talk_label.setAlignment(Qt.AlignCenter)
        self.talk_label.hide()

        # 动画标签
        self.image_label = QLabel(self)
        self._play_animation(self._get_idle_animation())

        # 布局 - 紧凑排列
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(5)
        layout.addWidget(self.talk_label, alignment=Qt.AlignCenter)
        layout.addWidget(self.image_label, alignment=Qt.AlignCenter)

        # 加载资源
        self._load_idle_resources()

        # 设置大小 - 根据内容自适应
        self.adjustSize()
        self._random_position()

    def _get_idle_animation(self):
        """获取待机动画"""
        idle_config = self.states.get(self.STATE_IDLE, {})
        animations = idle_config.get("animations", [])

        if animations:
            return random.choice(animations)

        # 使用默认目录
        anim_dir = "assets/pikaqiu"
        if not os.path.exists(anim_dir):
            anim_dir = "pikaqiu"

        if os.path.exists(anim_dir):
            files = [os.path.join(anim_dir, f) for f in os.listdir(anim_dir) if f.endswith(".gif")]
            if files:
                return random.choice(files)

        return "assets/pikaqiu/pikaqiu1.gif"

    def _load_idle_resources(self):
        """加载待机资源"""
        # 加载待机动画列表
        idle_config = self.states.get(self.STATE_IDLE, {})
        self.idle_animations = idle_config.get("animations", [])

        if not self.idle_animations:
            anim_dir = "assets/pikaqiu"
            if not os.path.exists(anim_dir):
                anim_dir = "pikaqiu"
            if os.path.exists(anim_dir):
                self.idle_animations = [os.path.join(anim_dir, f) for f in os.listdir(anim_dir) if f.endswith(".gif")]

        if not self.idle_animations:
            self.idle_animations = ["assets/pikaqiu/pikaqiu1.gif"]

        # 加载待机对话列表
        self.idle_dialogs = idle_config.get("dialogs", [])
        if not self.idle_dialogs:
            dialog_file = "assets/dialog.txt"
            if not os.path.exists(dialog_file):
                dialog_file = "dialog.txt"
            try:
                with open(dialog_file, "r", encoding="utf-8") as f:
                    self.idle_dialogs = [line for line in f.read().split("\n") if line.strip()]
            except:
                self.idle_dialogs = ["皮卡皮卡~"]

    def _play_animation(self, anim_path):
        """播放动画（统一缩放）"""
        if os.path.exists(anim_path):
            self.movie = QMovie(anim_path)
            self.movie.setScaledSize(QSize(self._pet_size, self._pet_size))
            self.image_label.setMovie(self.movie)
            self.movie.start()
        else:
            # 尝试默认路径
            default = "assets/pikaqiu/pikaqiu1.gif"
            if not os.path.exists(default):
                default = "pikaqiu/pikaqiu1.gif"
            if os.path.exists(default):
                self.movie = QMovie(default)
                self.movie.setScaledSize(QSize(self._pet_size, self._pet_size))
                self.image_label.setMovie(self.movie)
                self.movie.start()

    def _show_state(self, state_name):
        """显示指定状态"""
        state_config = self.states.get(state_name, DEFAULT_STATES.get(state_name, {}))

        # 播放动画
        anim_path = state_config.get("animation", "")
        if anim_path:
            self._play_animation(anim_path)

        # 显示对话
        dialog = state_config.get("dialog", "")
        if dialog:
            self.talk_label.setText(dialog)

            # 计算字体大小
            font_size = max(10, int(self._pet_size / 12))

            # 应用样式
            style = state_config.get("style", "")
            if style:
                self.talk_label.setStyleSheet(f"""
                    QLabel {{
                        font-family: 'Microsoft YaHei UI';
                        font-size: {font_size}px;
                        border: none;
                        border-radius: 10px;
                        padding: 6px 10px;
                        {style}
                    }}
                """)
            else:
                self.talk_label.setStyleSheet(f"""
                    QLabel {{
                        font-family: 'Microsoft YaHei UI';
                        font-size: {font_size}px;
                        color: #333;
                        background-color: white;
                        border: 1px solid #FFD93D;
                        border-radius: 10px;
                        padding: 6px 10px;
                    }}
                """)

            self.talk_label.adjustSize()
            self.talk_label.show()

    def _init_timers(self):
        """初始化定时器"""
        # 对话切换
        self.talk_timer = QTimer(self)
        self.talk_timer.timeout.connect(self._update_talk)
        self.talk_timer.start(6000)

        # 动画切换
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._update_animation)
        self.anim_timer.start(6000)

        # 休息提醒
        self.rest_timer = QTimer(self)
        self.rest_timer.timeout.connect(self._show_rest_reminder)

    def _random_position(self):
        """随机位置"""
        screen = QApplication.primaryScreen().geometry()
        x = int(random.random() * (screen.width() - self.width()))
        y = int(random.random() * (screen.height() - self.height()))
        self.move(x, y)

    def _update_talk(self):
        """更新对话"""
        if self._current_state == self.STATE_IDLE and self.idle_dialogs:
            text = random.choice(self.idle_dialogs)
            self.talk_label.setText(text)
            # 计算字体大小
            font_size = max(10, int(self._pet_size / 12))
            self.talk_label.setStyleSheet(f"""
                QLabel {{
                    font-family: 'Microsoft YaHei UI';
                    font-size: {font_size}px;
                    color: #333;
                    background-color: white;
                    border: 1px solid #FFD93D;
                    border-radius: 10px;
                    padding: 6px 10px;
                }}
            """)
            self.talk_label.adjustSize()
            self.talk_label.show()

    def _update_animation(self):
        """更新动画"""
        if self._current_state == self.STATE_IDLE and self.idle_animations:
            anim = random.choice(self.idle_animations)
            self._play_animation(anim)

    def _show_rest_reminder(self):
        """显示休息提醒"""
        self._current_state = self.STATE_REST
        self._show_state(self.STATE_REST)
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2,
        )

    def _reset_to_idle(self):
        """重置为待机状态"""
        self._current_state = self.STATE_IDLE
        if self.idle_animations:
            self._play_animation(random.choice(self.idle_animations))
        self.talk_label.hide()

    def mousePressEvent(self, event):
        """鼠标点击"""
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.pos()
            self._current_state = self.STATE_CLICK
            self._show_state(self.STATE_CLICK)
            event.accept()

    def mouseMoveEvent(self, event):
        """鼠标移动（拖拽）"""
        if event.buttons() == Qt.LeftButton and self._drag_pos:
            # 拖拽状态
            if self._current_state != self.STATE_DRAG:
                self._current_state = self.STATE_DRAG
                self._show_state(self.STATE_DRAG)
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        """鼠标释放"""
        self._drag_pos = None
        self._reset_to_idle()

    def enterEvent(self, event):
        """鼠标进入"""
        self.setCursor(QCursor(Qt.ClosedHandCursor))

    def contextMenuEvent(self, event):
        """右键菜单"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 24px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #FFF9E6;
            }
        """)

        hide_action = menu.addAction("隐藏")
        chat_action = menu.addAction(f"与 {self.persona_manager.name} 聊天")
        rest_text = "关闭休息提醒" if self._rest_enabled else "打开休息提醒"
        rest_action = menu.addAction(rest_text)
        menu.addSeparator()
        quit_action = menu.addAction("退出")

        action = menu.exec_(self.mapToGlobal(event.pos()))

        if action == quit_action:
            self._quit()
        elif action == hide_action:
            self.setWindowOpacity(0)
        elif action == chat_action:
            self._open_chat()
        elif action == rest_action:
            self._rest_enabled = not self._rest_enabled
            if self._rest_enabled:
                self.rest_timer.start(3600000)
            else:
                self.rest_timer.stop()

    def update_all_ui(self):
        """更新所有UI（人设名称变化时调用）"""
        # 更新宠物尺寸
        new_size = self.config.get("ui", {}).get("pet_size", 100)
        if new_size != self._pet_size:
            self._pet_size = new_size
            # 更新文字字体大小
            font_size = max(10, int(self._pet_size / 12))
            self.talk_label.setStyleSheet(f"""
                QLabel {{
                    font-family: 'Microsoft YaHei UI';
                    font-size: {font_size}px;
                    color: #333;
                    background-color: white;
                    border: 1px solid #FFD93D;
                    border-radius: 10px;
                    padding: 6px 10px;
                }}
            """)
            # 重新播放动画以应用新尺寸
            if self.idle_animations:
                self._play_animation(random.choice(self.idle_animations))
            # 重新调整窗口大小
            self.adjustSize()
        # 更新聊天窗口
        if self._chat_window:
            self._chat_window.update_persona_name(self.persona_manager.name)

    def _show_window(self):
        """显示窗口"""
        self.setWindowOpacity(1)
        self.show()

    def _open_chat(self):
        """打开聊天窗口"""
        # 每次打开重新创建窗口以应用最新配置
        if self._chat_window is not None:
            self._chat_window.close()
        self._chat_window = ChatWindow(
            self.config,
            self.chat_service,
            self.memory_manager,
            self.persona_manager,
        )
        self._chat_window.settings_requested.connect(self._open_settings)
        self._chat_window.show()
        self._chat_window.raise_()

    def _open_settings(self):
        """打开设置"""
        dialog = SettingsDialog(self.config, self._chat_window)
        if dialog.exec_():
            self.chat_service.update_config(self.config)
            # 重新加载状态配置
            self._load_states_config()
            self._load_idle_resources()
            # 更新所有UI
            self.update_all_ui()

    def _quit(self):
        """退出程序"""
        self.memory_manager.save_to_file()
        messages = self.memory_manager.get_messages()
        if len(messages) >= 4:
            self._do_summary_and_quit()
        else:
            ConfigLoader.save(self.config)
            QApplication.quit()

    def _do_summary_and_quit(self):
        """总结并退出"""
        self.talk_label.setText("正在整理记忆...")
        self.talk_label.show()
        QApplication.processEvents()

        messages = self.memory_manager.get_messages()
        worker = SummaryWorker(self.chat_service, messages)
        worker.finished.connect(lambda summary: self._on_summary_done(summary))
        worker.run()

    def _on_summary_done(self, summary: str):
        """总结完成"""
        if summary:
            lines = [l.strip("- ") for l in summary.split("\n") if l.strip()]
            for line in lines[:5]:
                if line and len(line) < 50:
                    self.persona_manager.add_preference(line)
        ConfigLoader.save(self.config)
        QApplication.quit()


def main():
    """主入口"""
    app = QApplication(sys.argv)
    pet = DesktopPet()
    pet.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()