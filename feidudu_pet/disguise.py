"""伪装：肥嘟嘟藏起来，变成一个卡通皮肤的输入法状态栏，同事路过看不出来。

皮肤没有框，只有一只蜡笔画的肥嘟嘟（sprites/skin.png，画法在 art-source/skin.js），
顺着它背上的弧线浮着几个小圆按钮：中/英、全半角（弯月亮/圆）、表情、设置。
「中」和全半角点了会像真的一样切换；整只可以拖到别处（位置会记住）。
双击肥嘟嘟，或者右键「还原」，肥嘟嘟就回来。
"""
from PyQt6.QtCore import QPoint, QPointF, Qt
from PyQt6.QtGui import QColor, QCursor, QPainter
from PyQt6.QtWidgets import QWidget

from .menu import crayon_menu
from .lang import tr
from .win32 import no_activate


class ImeBar(QWidget):
    def __init__(self, skin, on_restore, on_moved):
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
                         | Qt.WindowType.Tool | Qt.WindowType.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setWindowTitle(tr("输入法", "Input method"))
        self.setMouseTracking(True)
        self.skin = skin
        self.setFixedSize(*[int(v) for v in skin["size"]])
        self.on_restore = on_restore          # 叫肥嘟嘟回来
        self.on_moved = on_moved              # 拖到新位置以后，存下来
        self.chinese = True
        self.full_width = False           # 全角/半角，默认半角（弯月亮）
        self.hover = None
        self.pressed = None
        self.drag_from = None
        self.dragged = False

    def item_at(self, pos):
        """鼠标在哪个圆按钮上。"""
        for name, rect in self.skin["cells"].items():
            d = QPointF(pos) - rect.center()
            if d.x() ** 2 + d.y() ** 2 <= (rect.width() / 2) ** 2:
                return name
        return None

    # ---------- 鼠标：拖动、点按钮、双击肥嘟嘟

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_from = event.globalPosition().toPoint() - self.pos()
            self.dragged = False
            self.pressed = self.item_at(event.position())
            self.update()

    def mouseMoveEvent(self, event):
        if self.drag_from is not None:
            target = event.globalPosition().toPoint() - self.drag_from
            if self.dragged or (target - self.pos()).manhattanLength() > 3:
                self.dragged = True
                self.move(target)
            return
        item = self.item_at(event.position())
        if item != self.hover:
            self.hover = item
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton or self.drag_from is None:
            return
        self.drag_from = None
        if self.dragged:
            self.on_moved(self.pos())
        elif self.pressed == self.item_at(event.position()):
            if self.pressed == "lang":
                self.chinese = not self.chinese
            elif self.pressed == "width":
                self.full_width = not self.full_width
        self.pressed = None
        self.update()

    def mouseDoubleClickEvent(self, event):
        pos = event.position()
        if self.skin["pet"].contains(QPointF(pos)) and self.item_at(pos) is None:
            self.on_restore()

    def leaveEvent(self, event):
        self.hover = None
        self.update()

    def contextMenuEvent(self, event):
        menu = crayon_menu()
        menu.addAction(tr("还原", "Restore"), self.on_restore)
        menu.exec(QCursor.pos())

    def showEvent(self, event):
        no_activate(self)
        super().showEvent(event)

    # ---------- 画

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.drawPixmap(QPointF(0, 0), self.skin["card"])
        for name in (self.hover, self.pressed):                  # 鼠标停在按钮上：淡淡的绿底
            if name:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QColor(79, 138, 62, 70 if name == self.pressed else 45))
                p.drawEllipse(self.skin["cells"][name].adjusted(1.5, 1.5, -1.5, -1.5))
        glyphs = self.skin["glyphs"]
        for name, key in (("lang", "lang_zh" if self.chinese else "lang_en"),
                          ("width", "width_full" if self.full_width else "width_half")):
            g = glyphs[key]
            c = self.skin["cells"][name].center()
            p.drawPixmap(QPointF(c.x() - g.width() / g.devicePixelRatio() / 2,
                                 c.y() - g.height() / g.devicePixelRatio() / 2), g)
        p.end()


def default_spot(area, bar):
    """真的输入法浮动栏常在右下角、任务栏上面一点。"""
    return QPoint(area.right() - bar.width() - 120, area.bottom() - bar.height() - 36)
