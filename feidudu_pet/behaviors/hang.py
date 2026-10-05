"""吊在丝上：嘴巴挂着一根丝往下垂，碰到活动窗口的上沿或者任务栏就降落。"""
import math
import random

from PyQt6.QtCore import QPointF

from . import register
from .base import Behavior
from .. import world
from ..config import SILK_FAST, SILK_SPEED


@register
class Hang(Behavior):
    name = "hang"
    anim = "hang"
    frame_every = 3
    duration = None

    def enter(self, pet, top=None, fast=False, **kw):
        pet.surface, pet.on_window, pet.win_edge = "air", False, None
        pet.silk_top = QPointF(top)
        pet.ax, pet.ay = top.x(), top.y() + 6 * pet.scale()
        pet.silk_fast = fast
        pet.silk_pause = 0
        if not fast:
            pet.say("zip", 1.2)

    def tick(self, pet):
        s = pet.scale()
        target, is_window = world.landing_target(pet)
        if pet.silk_pause > 0:                         # 偶尔停一下，晃一晃
            pet.silk_pause -= 1
            return
        if not pet.silk_fast and random.random() < 0.01:
            pet.silk_pause = random.randint(8, 18)
        tail = pet.ay + pet.sp.hang_len * s
        speed = SILK_FAST * s if pet.silk_fast and target - tail > 60 * s else SILK_SPEED * s
        pet.ay += speed
        if pet.ay + pet.sp.hang_len * s >= target:
            world.land(pet, target, is_window, hard=pet.silk_fast)

    def exit(self, pet):
        pet.silk.hide()

    def frame(self, pet):
        return self.anim, pet.tick // self.frame_every, QPointF(pet.ax, pet.ay), 0, False

    def silk_line(self, pet):
        """丝从哪到哪、晃多少。"""
        return pet.silk_top, QPointF(pet.ax, pet.ay), 6 * math.sin(pet.tick / 6)
