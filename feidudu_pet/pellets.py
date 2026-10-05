"""便便（frass）：一颗一颗的小窗口，从尾巴那儿掉下来，落在任务栏上。点一下就捡起来，攒着当花肥。"""
import random

from PyQt6.QtCore import QPoint, QPointF, Qt
from PyQt6.QtGui import QGuiApplication, QPainter
from PyQt6.QtWidgets import QWidget

from .config import FRASS_GRAVITY
from .win32 import no_activate


class Pellet(QWidget):
    def __init__(self, pixmap, pos, scale, on_pick):
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
                         | Qt.WindowType.Tool | Qt.WindowType.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setCursor(Qt.CursorShape.PointingHandCursor)       # 看得出来能点
        self.pix = pixmap
        self.k = scale
        self.tilt = random.uniform(-18, 18)
        self.half = pixmap.height() / pixmap.devicePixelRatio() * scale * 0.33   # 中心到底面（画面四周有留白）
        self.cx, self.cy = pos.x(), pos.y()          # 中心在屏幕上的位置
        self.vy = 0.0
        self.bounced = False
        self.landed = False
        self.on_pick = on_pick
        side = int(pixmap.width() / pixmap.devicePixelRatio() * scale) + 6
        self.setFixedSize(side, side)
        self.place()
        self.show()

    def floor(self):
        """正下方任务栏的上沿。"""
        screen = QGuiApplication.screenAt(QPoint(int(self.cx), int(self.cy))) or QGuiApplication.primaryScreen()
        return screen.availableGeometry().bottom() + 1

    def fall(self):
        """每拍往下掉一点；落地轻轻弹一下就躺平。"""
        if self.landed:
            return
        self.vy += FRASS_GRAVITY * self.k
        self.cy += self.vy
        bottom = self.floor()
        if self.cy + self.half >= bottom:
            self.cy = bottom - self.half
            if not self.bounced and self.vy > 4:
                self.vy = -self.vy * 0.3
                self.bounced = True
            else:
                self.landed = True
        self.place()

    def place(self):
        self.move(int(self.cx - self.width() / 2), int(self.cy - self.height() / 2))

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.translate(self.width() / 2, self.height() / 2)
        p.rotate(self.tilt)
        p.scale(self.k, self.k)
        w = self.pix.width() / self.pix.devicePixelRatio()
        h = self.pix.height() / self.pix.devicePixelRatio()
        p.drawPixmap(QPointF(-w / 2, -h / 2), self.pix)
        p.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.on_pick(self)

    def showEvent(self, event):
        no_activate(self)
        super().showEvent(event)
