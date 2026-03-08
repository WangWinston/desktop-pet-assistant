# macOS 斜杠命令弹窗兼容性修复设计

## 问题描述

在 macOS 上，聊天窗口输入框中输入 `/` 无法唤醒命令列表弹窗。

## 根因分析

1. 主窗口使用了 `Qt.Tool` 标志以兼容 macOS（`chat_window.py:723-726`）
2. `_skills_popup` 作为 `self.container` 的子控件创建
3. 在 macOS 上，带有 `Qt.Tool` 标志的窗口的子控件可能存在层级显示问题
4. `textChanged` 信号正常触发（回车发送功能正常），问题出在弹窗显示机制

## 解决方案

将技能列表弹窗改为独立的 `Qt.Popup` 窗口，确保在 macOS 上正确显示在最顶层。

## 设计详情

### 修改 `_ensure_skills_popup` 方法

将 `QListWidget(self.container)` 改为独立的 `QListWidget()`，并设置 `Qt.Popup | Qt.FramelessWindowHint` 窗口标志。

```python
def _ensure_skills_popup(self):
    """延迟创建技能列表弹窗"""
    if self._skills_popup is not None:
        return

    # 创建独立的 Popup 窗口（无父控件）
    self._skills_popup = QListWidget()
    self._skills_popup.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
    # ... 其他样式设置保持不变
```

### 修改 `_on_input_changed` 方法中的位置计算

使用 `mapToGlobal` 将局部坐标转换为全局坐标，确保弹窗定位正确。

```python
# 获取输入框在窗口中的位置
input_geo = self.message_input.geometry()
bar_geo = self.input_bar.geometry()

popup_width = input_geo.width()
popup_height = min(180, 30 + 26 * len(matched_items))

# 转换为全局坐标
global_pos = self.mapToGlobal(QPoint(bar_geo.x() + input_geo.x(), bar_geo.y()))

x = global_pos.x()
y = global_pos.y() - popup_height - 6
if y < 0:
    y = global_pos.y() + input_geo.height() + 6  # 显示在输入框下方

self._skills_popup.setGeometry(x, y, popup_width, popup_height)
self._skills_popup.show()
```

### 添加必要的导入

在文件顶部添加 `QPoint` 的导入（如果尚未导入）。

## 优点

- `Qt.Popup` 在 macOS 上会正确显示在最顶层
- 点击窗口外部会自动关闭弹窗
- 不受主窗口 `Qt.Tool` 标志影响
- 跨平台兼容性更好

## 影响范围

仅修改 `ui/chat_window.py` 文件中的弹窗相关代码，不影响其他功能。