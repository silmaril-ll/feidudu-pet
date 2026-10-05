"""那根丝：单独一个透明、点不到的小窗口，只负责画线。"""
from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QWidget

from .win32 import no_activate


class SilkThread(QWidget):
    """单独一个透明、点不到的小窗口，只负责画那根丝。"""

    def __init__(self):
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
                         | Qt.WindowType.Tool | Qt.WindowType.WindowTransparentForInput
                         | Qt.WindowType.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.top = QPointF()
        self.bottom = QPointF()
        self.sway = 0.0

    def set_line(self, top, bottom, sway):
        self.top, self.bottom, self.sway = QPointF(top), QPointF(bottom), sway
        pad = 12
        x0 = min(top.x(), bottom.x()) - pad
        self.setGeometry(int(x0), int(top.y()) - 2, int(abs(top.x() - bottom.x()) + 2 * pad), int(bottom.y() - top.y()) + 4)
        if not self.isVisible():
            self.show()
            no_activate(self)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        origin = QPointF(self.x(), self.y())
        a, b = self.top - origin, self.bottom - origin
        path = QPainterPath(a)
        path.quadTo(QPointF((a.x() + b.x()) / 2 + self.sway, (a.y() + b.y()) / 2), b)
        p.setPen(QPen(QColor(60, 50, 40, 70), 2.6))
        p.drawPath(path)
        p.setPen(QPen(QColor(255, 253, 245, 235), 1.3))
        p.drawPath(path)
        p.end()
