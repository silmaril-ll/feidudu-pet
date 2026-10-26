"""喝露水：它自己偶尔在脚边发现几颗小露珠（“露水！”），低头咕嘟咕嘟一颗颗喝掉，“解渴～”。
真的毛毛虫会喝叶子上的露水，所以早上（DEW_HOURS）更容易碰到；喝过一次至少隔 DEW_AGAIN 分钟。
露珠垫在身体下面画（Behavior.under），低头喝用吃叶子（munch）的嚼的帧。"""
import random
import time

from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QPainter, QPixmap

from . import register
from .base import Behavior
from ..clock import now
from ..config import DEW_AGAIN, DEW_HOURS, DEW_MORNING, DEW_OTHER

NOTICE, SIP = 14, 42          # 先看一会儿，再一共喝几拍
DROPS = 3
_pics = {}                    # 剩几颗露珠的样子，画一次存着


def drops_pixmap(pet, left):
    """left 颗露珠排在一起的小图（2 倍图），每颗大小不太一样。"""
    if left not in _pics:
        r = pet.sp.ratio
        pix = QPixmap(int(58 * r), int(24 * r))
        pix.setDevicePixelRatio(r)
        pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        for i, (x, k) in enumerate(((2, 1.3), (20, 1.6), (40, 1.15))[:left]):
            drop = pet.sp.drops[i % len(pet.sp.drops)]
            w, h = drop.width() / drop.devicePixelRatio() * k, drop.height() / drop.devicePixelRatio() * k
            p.drawPixmap(QPointF(x, 24 - h).toPoint(), drop.scaled(int(w * r), int(h * r), transformMode=Qt.TransformationMode.SmoothTransformation))
        p.end()
        _pics[left] = pix
    return _pics[left]


@register
class Dew(Behavior):
    name = "dew"
    anim = "munch"
    frame_every = 2
    duration = None

    def weight_for(self, pet):
        if pet.surface != "floor" or pet.toy or time.time() < pet.dew_next:
            return 0
        start, end = DEW_HOURS
        return DEW_MORNING if start <= now().hour < end else DEW_OTHER

    def enter(self, pet, **kw):
        pet.dew_left = DROPS
        pet.dew_next = time.time() + DEW_AGAIN * 60
        pet.say("dew", 1.6)

    def tick(self, pet):
        t = pet.tick - NOTICE
        if t == 0:
            pet.say("gulp", 2.4)
        if t > 0 and t % (SIP // DROPS) == 0:
            pet.dew_left = max(0, pet.dew_left - 1)
        if t >= SIP:
            pet.say("quenched", 1.8)
            pet.start("idle", random.uniform(3, 6))

    def under(self, pet, index):
        if pet.dew_left <= 0:
            return None
        foot = pet.sp.anims[self.anim].anchor
        return drops_pixmap(pet, pet.dew_left), QPointF(foot.x() - 128, foot.y() - 18)     # 嘴前面的地上（近的先喝掉）

    def frame(self, pet):
        name, i, here, deg, mirrored = super().frame(pet)
        if pet.tick < NOTICE:
            return "idle", pet.tick // 2, here, deg, mirrored          # 先看一会儿
        return name, (pet.tick - NOTICE) // self.frame_every, here, deg, mirrored
