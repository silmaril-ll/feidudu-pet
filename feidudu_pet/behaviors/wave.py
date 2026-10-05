"""探路：后脚抓牢，抬起前半身左右晃一晃，找下一个落脚的地方。
真的毛毛虫爬到叶子边上就会这样。到了边上（world.wave_first）会先晃一晃再决定往哪走；平时偶尔也晃。"""
import random

from PyQt6.QtCore import QPointF

from . import pick_next, register
from .base import Behavior
from .. import world

RISE, SWAY = 3, 8          # wave 画面：前 3 帧是抬起来（倒着放就是放下），后 8 帧是晃


@register
class Wave(Behavior):
    name = "wave"
    anim = "wave"
    frame_every = 2
    duration = None

    def weight_for(self, pet):
        return 0.06 if pet.surface == "floor" else 0

    def enter(self, pet, edge=False, **kw):
        sway = list(range(RISE, RISE + SWAY)) * random.choice((1, 2))
        pet.wave_seq = list(range(RISE)) + sway + list(reversed(range(RISE)))
        pet.wave_edge = edge
        if random.random() < 0.35:
            pet.say("hmm", 1.4)

    def tick(self, pet):
        if pet.tick >= len(pet.wave_seq) * self.frame_every:
            if pet.wave_edge:                         # 探完路，接着爬，这次真的决定往哪走
                pet.start("crawl", random.uniform(4, 12), waved=True)
            else:
                pick_next(pet)

    def frame(self, pet):
        deg, mirrored = world.pose_transform(pet)
        i = pet.wave_seq[min(pet.tick // self.frame_every, len(pet.wave_seq) - 1)]
        return self.anim, i, QPointF(pet.ax, pet.ay), deg, mirrored
