"""陪你忙：你在忙（senses.busy，最近一分钟一直在打字、滚网页）的时候，它更想去活动窗口上；
在窗口上沿会躲到窗口后面，只露出脑袋和两只扒着边的小脚，偷偷看你在做什么（peek）。
你忙了好一阵停下来，它问“忙完啦？”；连着忙太久，它提醒你“歇一下？”（右键菜单里可以关）。
peek 画面是正面的肥嘟嘟：前 3 帧慢慢冒出来，后 6 帧看着你轻轻晃，最后倒着放缩回去。"""
import random
import time

from PyQt6.QtCore import QPointF

from . import pick_next, register
from .base import Behavior
from .. import world
from ..config import BREAK_AFTER, BREAK_AGAIN, BUSY_PEEK, DONE_AFTER

RISE, WATCH = 3, 6


def check_in(pet):
    """每拍看一眼：你刚忙完，或者忙太久了，就跟你说一声（睡着、被拎着这些时候不说）。"""
    senses, now = pet.senses, time.time()
    calm = pet.state in ("idle", "crawl", "peek", "look")
    if senses.done_busy >= DONE_AFTER and calm:
        return greet(pet, "done")
    if (pet.save.get("break_reminder", True) and senses.busy and calm
            and now - senses.busy_since >= BREAK_AFTER and now >= pet.rest_next):
        pet.rest_next = now + BREAK_AGAIN
        greet(pet, "rest")


def greet(pet, bubble):
    """抬起前半身晃一晃（引起你注意），说句话。"""
    if pet.surface == "floor":
        pet.start("wave")
    pet.say(bubble, 3)


@register
class Peek(Behavior):
    name = "peek"
    anim = "peek"
    frame_every = 3
    duration = None

    def weight_for(self, pet):
        return BUSY_PEEK if pet.senses.busy and pet.on_window and pet.win_edge == "top" else 0

    def enter(self, pet, **kw):
        watch = list(range(RISE, RISE + WATCH)) * random.randint(3, 6)
        pet.peek_seq = list(range(RISE)) + watch + list(reversed(range(RISE)))
        if random.random() < 0.3:
            pet.say("busy", 2)

    def tick(self, pet):
        if pet.tick >= len(pet.peek_seq) * self.frame_every:
            pick_next(pet)

    def frame(self, pet):
        deg, mirrored = world.pose_transform(pet)
        i = pet.peek_seq[min(pet.tick // self.frame_every, len(pet.peek_seq) - 1)]
        return self.anim, i, QPointF(pet.ax, pet.ay), deg, mirrored
