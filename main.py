#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
桌面宠物 - 主入口

一只可爱的桌面宠物，支持：
- OpenAI 兼容 API 聊天
- 上下文记忆和自动压缩
- 人设和用户偏好设置
- 休息提醒功能
"""
import sys

from PyQt5.QtWidgets import QApplication
from ui.pet import main

if __name__ == "__main__":
    main()