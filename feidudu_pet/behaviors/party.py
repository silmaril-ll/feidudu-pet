"""庆祝：每吃满 PARTY_EVERY（一百）片叶子，面前立起一个礼花筒，“砰”地喷出彩纸（confetti.py），
它开心地抬起前半身晃一晃，泡泡里写“第100片！”。庆祝完再接着吃完叶子该做的事（特别叶子的效果、好吃、打嗝）。
抬身子晃用的是探路（wave）的画面。"""
import random

from PyQt6.QtCore import QPointF

from . import register
from .base import Behavior
from .munch import after_meal
from .wave import RISE, SWAY
from .. import world

POPPER_AT = -84             # 礼花筒立在头前面多远（脚底支点的坐标，1 倍大小；头在 -61）


@register
class Party(Behavior):
    name = "party"
    anim = "wave"
    frame_every = 2
    duration = None

    def enter(self, pet, count=100, leaf=None, full=False, **kw):
        pet.party_after = (leaf, full)
        pet.party_seq = list(range(RISE)) + list(range(RISE, RISE + SWAY)) * 3 + list(reversed(range(RISE)))
        pet.confetti.burst(world.local_to_world(pet, POPPER_AT, 0), pet.dir, pet.scale())
        bubble = f"leaves_{count}"
        pet.say(bubble if bubble in pet.sp.bubbles else "leaves_more", 4)

    def tick(self, pet):
        if pet.tick >= len(pet.party_seq) * self.frame_every:
            leaf, full = pet.party_after
            if leaf is None:
                return pet.start("idle", random.uniform(3, 6))
            after_meal(pet, leaf, full)

    def frame(self, pet):
        deg, mirrored = world.pose_transform(pet)
        i = pet.party_seq[min(pet.tick // self.frame_every, len(pet.party_seq) - 1)]
        return self.anim, i, QPointF(pet.ax, pet.ay), deg, mirrored
