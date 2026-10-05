"""丝垫：真的毛毛虫边爬边吐丝铺在脚下，脚才抓得牢。常走的地方丝会越积越多。

肥嘟嘟在任务栏上、活动窗口上沿爬的时候，会一根一根记下铺过的丝。
画丝的是两条细细的、点不到的透明窗口：一条贴着任务栏，一条贴着当前活动窗口的上沿。
丝只记在这次运行里（窗口编号每次开机都不一样）。
"""
import random

from PyQt6.QtCore import QPointF, QRect, Qt
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QWidget

from . import world
from .config import SILK_PLACES, SILK_STRANDS
from .win32 import no_activate

STRIP = 8          # 画丝的窗口有多高：面往上 6 像素、往下 2 像素


class SilkMat(QWidget):
    def __init__(self):
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
                         | Qt.WindowType.Tool | Qt.WindowType.WindowTransparentForInput
                         | Qt.WindowType.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.strands = []
        self.origin = 0

    def show_strands(self, strands, origin, left, y, width):
        """strands 里的 x 都是减掉 origin 之后的；这条窗口从 left 开始、宽 width，贴着 y 这条线。"""
        self.strands, self.origin = strands, origin
        rect = QRect(int(left), int(y) - STRIP + 2, int(width), STRIP)
        if self.geometry() != rect:
            self.setGeometry(rect)
        shown = not self.isVisible()
        if shown:
            self.show()
            no_activate(self)
        self.update()
        return shown

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        base = STRIP - 2.5
        shift = self.origin - self.x()
        for x0, x1, seed, _ in self.strands:
            a, b = sorted((x0 + shift, x1 + shift))
            if b - a < 4:
                continue
            r = random.Random(seed)                  # 同一根丝每次画得一样，不会闪
            path = QPainterPath(QPointF(a, base - r.uniform(0, 1.5)))
            path.quadTo(QPointF((a + b) / 2, base - r.uniform(-1, 3)), QPointF(b, base - r.uniform(0, 1.5)))
            p.setPen(QPen(QColor(60, 50, 40, 30), 2.4))
            p.drawPath(path)
            p.setPen(QPen(QColor(255, 253, 245, 170), 1.2))
            p.drawPath(path)
        p.end()


class SilkTrail:
    def __init__(self):
        self.places = {}          # "floor" 或窗口编号 -> [[起点 x, 终点 x, 随机种子, 方向], ...]
        self.current = None       # 正在铺的那根丝：(地方, 丝)
        self.floor_mat = SilkMat()
        self.window_mat = SilkMat()

    def lay(self, pet):
        """爬了一拍：接着把脚下这根丝往前铺，换了地方或者掉了头就开一根新的。"""
        if pet.surface != "floor" or (pet.on_window and pet.win is None):
            self.current = None
            return
        key = pet.win_hwnd if pet.on_window else "floor"
        x = pet.ax - (pet.win.left() if pet.on_window else 0)
        strand = self.current[1] if self.current and self.current[0] == key else None
        if strand and strand[3] == pet.dir and abs(strand[1] - x) < 10:
            strand[1] = x
            return
        strands = self.places.pop(key, [])
        self.places[key] = strands                   # 挪到最后，算“最近去过”
        strand = [x, x, random.randrange(1 << 30), pet.dir]
        strands.append(strand)
        del strands[:-SILK_STRANDS]
        while len(self.places) > SILK_PLACES:
            self.places.pop(next(iter(self.places)))
        self.current = (key, strand)

    def stop(self):
        self.current = None

    def show(self, pet):
        """把两条丝垫挪到任务栏、活动窗口上沿；新露出来的时候让肥嘟嘟站回丝上面。"""
        shown = False
        a = world.area()
        if self.places.get("floor"):
            shown |= self.floor_mat.show_strands(self.places["floor"], 0, a.left(), a.bottom() + 1, a.width())
        w, hwnd = pet.win, pet.active_hwnd
        if w is not None and self.places.get(hwnd):
            shown |= self.window_mat.show_strands(self.places[hwnd], w.left(), w.left(), w.top(), w.width())
        elif self.window_mat.isVisible():
            self.window_mat.hide()
        if shown:
            pet.raise_()
