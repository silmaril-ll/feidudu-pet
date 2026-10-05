"""梦蝶（二）：变成柑橘凤蝶，在屏幕上飘来飘去飞一会儿；时间到了飞回任务栏，
落地又变回肥嘟嘟，说“做了个梦…”。飞的时候点不到、拎不起来（在做梦呢）。"""
import math
import random
import time

from PyQt6.QtCore import QPointF

from . import register
from .base import Behavior
from .. import world
from ..config import FLY_SPEED


@register
class Butterfly(Behavior):
    name = "butterfly"
    anim = "fly"
    duration = None

    def enter(self, pet, minutes=10, **kw):
        pet.surface, pet.on_window, pet.win_edge = "air", False, None
        pet.fly_until = time.time() + minutes * 60
        pet.fly_vx = 0.0
        pet.ay -= 40 * pet.scale()                  # 从蛹那里飞起来
        self.new_target(pet)

    def new_target(self, pet):
        a = world.area()
        pet.fly_target = QPointF(random.uniform(a.left() + 120, a.right() - 120),
                                 random.uniform(a.top() + 120, a.bottom() - 160))

    def tick(self, pet):
        landing = time.time() > pet.fly_until
        a = world.area()
        if landing:                                  # 该醒了：飞回任务栏
            pet.fly_target = QPointF(min(max(pet.ax, a.left() + 150), a.right() - 150), a.bottom() + 1)
        d = pet.fly_target - QPointF(pet.ax, pet.ay)
        dist = math.hypot(d.x(), d.y())
        step = FLY_SPEED * pet.scale()
        if dist < step * 2:
            if landing:
                return self.wake(pet, a)
            self.new_target(pet)
            return
        pet.fly_vx = d.x() / dist * step
        pet.ax += pet.fly_vx
        pet.ay += d.y() / dist * step + 2.2 * math.sin(pet.tick / 3)   # 一上一下地飘
        if not landing and random.random() < 0.004:
            self.new_target(pet)                    # 忽然换个方向

    def wake(self, pet, a):
        pet.surface = "floor"
        pet.ay = a.bottom() + 1
        pet.start("idle", 6)
        pet.say("dream", 3)

    def frame(self, pet):
        tilt = max(-18, min(18, pet.fly_vx * 5))
        return self.anim, pet.tick, QPointF(pet.ax, pet.ay), tilt, False
