"""礼花：每吃满一百片叶子，肥嘟嘟面前立起一个礼花筒，“砰”地喷出一把彩纸和彩带。
单独一个透明、点不到的大窗口（和丝一样），只在放礼花的这几秒里开着、按自己的节拍动，放完就藏起来。
礼花筒和彩纸是 art-source/pet.js 里画的（popperPic、confettiPics）。"""
import math
import random

from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer
from PyQt6.QtGui import QPainter, QTransform
from PyQt6.QtWidgets import QWidget

from .win32 import no_activate

FRAME_MS = 33                 # 放礼花的时候一秒 30 帧（平时的一拍 90 毫秒，彩纸飞起来不够顺）
POP_AT = 0.55                 # 立起来多少秒以后“砰”
LASTS = 4.5                   # 一共放多少秒
TIP = QPointF(30, 60)         # 礼花筒画面里筒尖在哪（逻辑像素）
MOUTH = 40.8                  # 筒尖到筒口多远
PIECES = 110                  # 喷出多少片
GRAVITY = 650                 # 往下掉的加速度（像素/秒²，1 倍大小）
FALL = 110                    # 纸片飘下来最快多快（像素/秒）：纸很轻，掉不快


class Confetti(QWidget):
    def __init__(self, sprites):
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
                         | Qt.WindowType.Tool | Qt.WindowType.WindowTransparentForInput
                         | Qt.WindowType.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.popper = sprites.popper
        self.pics = sprites.confetti
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.step)
        self.pieces = []
        self.t = 0.0

    def burst(self, ground, direction, scale):
        """在 ground（屏幕上的一个点，礼花筒尖立在这）放一次礼花；direction 是筒口往哪边歪（+1 右，-1 左）。"""
        self.k = max(scale, 0.6)
        self.tip = QPointF(ground)
        self.tilt = 22 * direction
        self.t, self.pieces, self.popped = 0.0, [], False
        w, h = int(760 * self.k), int(660 * self.k)
        self.setGeometry(int(ground.x() - w / 2), int(ground.y() - h + 30 * self.k), w, h)
        self.show()
        no_activate(self)
        self.timer.start(FRAME_MS)

    def mouth(self):
        a = math.radians(self.tilt + self.recoil())
        r = MOUTH * self.k
        return QPointF(self.tip.x() + r * math.sin(a), self.tip.y() - r * math.cos(a))

    def recoil(self):
        """“砰”的时候筒子往后一抖。"""
        since = self.t - POP_AT
        return -10 * math.exp(-since * 9) * math.cos(since * 30) * (1 if self.tilt > 0 else -1) if since > 0 else 0

    def pop(self):
        self.popped = True
        m, k = self.mouth(), self.k
        up = math.radians(self.tilt)
        for _ in range(PIECES):
            pic = random.randrange(len(self.pics))
            streamer = pic >= len(self.pics) - 6                # 最后 6 张是卷卷的彩带：飘得慢一点
            a = up + random.gauss(0, 0.38)
            v = random.uniform(450, 950) * k * (0.75 if streamer else 1)
            self.pieces.append({"pic": pic, "x": m.x(), "y": m.y(), "vx": v * math.sin(a), "vy": -v * math.cos(a),
                                "rot": random.uniform(0, 360), "spin": random.uniform(-540, 540),
                                "drag": 0.93 if streamer else 0.96, "s": random.uniform(1.1, 1.7) * k,
                                "phase": random.uniform(0, 6.3), "sway": random.uniform(20, 60) * k})

    def step(self):
        dt = FRAME_MS / 1000
        self.t += dt
        if not self.popped and self.t >= POP_AT:
            self.pop()
        for p in self.pieces:
            p["vy"] += GRAVITY * self.k * dt
            p["vx"] *= p["drag"]
            p["vy"] *= p["drag"]
            p["vy"] = min(p["vy"], FALL * self.k)               # 掉下来的时候慢慢飘
            flutter = p["sway"] * math.cos(self.t * 5 + p["phase"]) if p["vy"] > 0 else 0   # 左右飘
            p["x"] += (p["vx"] + flutter) * dt
            p["y"] += p["vy"] * dt
            p["rot"] += p["spin"] * dt
        if self.t >= LASTS:
            self.stop()
        self.update()

    def stop(self):
        self.timer.stop()
        self.pieces = []
        self.hide()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        origin = QPointF(self.x(), self.y())
        fade = min(1.0, (LASTS - self.t) / 0.7)                # 最后 0.7 秒慢慢淡掉
        p.setOpacity(max(0.0, fade) * min(1.0, self.t / 0.15))
        t = QTransform()                                        # 礼花筒：筒尖立在地上，斜着
        tip = self.tip - origin
        t.translate(tip.x(), tip.y())
        t.rotate(self.tilt + self.recoil())
        t.scale(self.k, self.k)
        t.translate(-TIP.x(), -TIP.y())
        p.setTransform(t)
        p.drawPixmap(QPointF(0, 0), self.popper)
        p.resetTransform()
        for piece in self.pieces:
            pic = self.pics[piece["pic"]]
            w, h = pic.width() / pic.devicePixelRatio(), pic.height() / pic.devicePixelRatio()
            p.save()
            p.translate(piece["x"] - origin.x(), piece["y"] - origin.y())
            p.rotate(piece["rot"])
            p.scale(piece["s"], piece["s"])
            p.drawPixmap(QRectF(-w / 2, -h / 2, w, h), pic, QRectF(pic.rect()))
            p.restore()
        p.end()
