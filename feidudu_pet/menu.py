"""蜡笔风格的右键菜单：还是 Qt 自己的菜单（子菜单、键盘、点外面关掉都照常），只是换了一身皮——
撕纸边的小卡片当底、鼠标停着的那一项抹一道绿蜡笔、蜡笔小箭头和勾、波浪分隔线。字用系统的，大小和平常的菜单一样。
画面在 art-source/menu.js。
"""
import json

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMenu

from .config import SPRITES

_style = None


def stylesheet():
    global _style
    if _style is None:
        info = json.loads((SPRITES / "sprites.json").read_text(encoding="utf-8"))["menu"]
        cut = info["cut"]

        def url(name):
            return '"' + (SPRITES / f"menu_{name}.png").as_posix() + '"'     # 加引号：路径里有空格也不会读错
        _style = f"""
            QMenu {{
                background: transparent;
                border-image: url({url("bg")}) {cut} {cut} {cut} {cut} stretch stretch;
                border-width: {cut - 4}px;
                font-family: "Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI", sans-serif;
                font-size: 9pt;
                color: #3b2f29;
            }}
            QMenu::item {{ padding: 4px 22px 4px 10px; background: transparent; }}
            QMenu::item:selected {{ border-image: url({url("hover")}) 0 0 0 0 stretch stretch; color: #2c3a22; }}
            QMenu::item:disabled {{ color: #b3aa9d; }}
            QMenu::separator {{ height: 6px; margin: 1px 4px; border-image: url({url("sep")}) 0 0 0 0 stretch stretch; }}
            QMenu::right-arrow {{ image: url({url("arrow")}); width: 10px; height: 10px; }}
            QMenu::indicator {{ width: 14px; height: 14px; }}
            QMenu::indicator:checked {{ image: url({url("check")}); }}
        """
    return _style


def crayon_menu(title="", parent=None):
    """一个蜡笔皮的菜单（透明的撕纸边，没有系统的方框和阴影）。"""
    menu = QMenu(title, parent)
    menu.setWindowFlags(menu.windowFlags() | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
    menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    menu.setStyleSheet(stylesheet())
    return menu


def add_submenu(menu, title):
    sub = crayon_menu(title, menu)
    menu.addMenu(sub)
    return sub
