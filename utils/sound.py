"""提示音管理模块"""
import sys
from PyQt5.QtCore import QObject


class SoundManager(QObject):
    """提示音管理器 - 使用系统内置提示音"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @staticmethod
    def play_notification():
        """播放普通提示音 - AI 回复完成"""
        from PyQt5.QtWidgets import QApplication
        QApplication.beep()

    @staticmethod
    def play_reminder():
        """播放提醒音 - 待办/休息提醒"""
        from PyQt5.QtWidgets import QApplication
        # macOS 使用更明显的系统通知音
        if sys.platform == 'darwin':
            import subprocess
            try:
                subprocess.run(['say', '-v', 'Bells', 'ding'], capture_output=True)
                return
            except Exception:
                pass
        QApplication.beep()

    @staticmethod
    def play_error():
        """播放错误音 - 错误提示"""
        from PyQt5.QtWidgets import QApplication
        # macOS 使用错误提示音
        if sys.platform == 'darwin':
            import subprocess
            try:
                subprocess.run(['say', '-v', 'Bells', 'basso'], capture_output=True)
                return
            except Exception:
                pass
        QApplication.beep()


# 全局单例
sound_manager = SoundManager()