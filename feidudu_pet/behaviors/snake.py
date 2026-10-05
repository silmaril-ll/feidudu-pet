"""蛇形警戒：连着戳它好几下，它就抬起前半身、把头缩起来、胸口鼓起来让假眼睛显得好大，
再冒出橙色小角——凤蝶幼虫真的会这样装成小蛇吓唬鸟。（pet.poke 里数戳了几下）"""
import random

from PyQt6.QtCore import QPointF

from . import register
from .base import Behavior
from .. import world

RISE, HOLD = 2, 4           # snake 画面：前 2 帧抬起来，后 4 帧停住轻轻晃


@register
class Snake(Behavior):
    name = "snake"
    anim = "snake"
    frame_every = 3
    duration = None

    def enter(self, pet, **kw):
        pet.say("hiss", 2)

    def tick(self, pet):
        if pet.tick >= (RISE + HOLD * 3) * self.frame_every:
            pet.start("idle", random.uniform(3, 6))

    def frame(self, pet):
        deg, mirrored = world.pose_transform(pet)
        step = pet.tick // self.frame_every
        i = step if step < RISE else RISE + (step - RISE) % HOLD
        return self.anim, i, QPointF(pet.ax, pet.ay), deg, mirrored
