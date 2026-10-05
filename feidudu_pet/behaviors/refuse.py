"""挑食：抽到不是芸香科的叶子（比如枫叶），叶子摆到它嘴前面，它凑过去闻一闻……
冒出小角、哼一声：才不吃！我只吃芸香科！——柑橘凤蝶的毛毛虫只吃芸香科（柑橘、花椒这一家）的叶子，别的再好看也不当饭。
然后叶子就摆在那儿，它嘟着嘴等你收拾，隔一会儿说一句“拿走！”。点一下那片叶子就拿走了（pet.mousePressEvent），
它说“这才对嘛”。一直没人管的话，过 REFUSE_WAIT 秒它自己扭过头去，叶子也就没了。花肥不扣。"""
import random

from PyQt6.QtCore import QPointF

from . import register
from .base import Behavior
from .. import world
from ..config import REFUSE_WAIT, TICK_MS

SNIFF = 16                  # 先闻多少拍（1 拍 90 毫秒）
HUFF = 18                   # 再冒小角哼多少拍
EXPLAIN = 22                # “我只吃芸香科！”说多久
NAG = 60                    # 等着的时候，隔多少拍说一句“拿走！”


@register
class Refuse(Behavior):
    name = "refuse"
    anim = "idle"
    frame_every = 2
    duration = None

    def enter(self, pet, leaf="maple", **kw):
        pet.leaf_kind = leaf
        pet.say("leaf_" + leaf, 1.6)                   # 枫叶！

    def waiting(self, pet):
        """闻过、哼过、说过了，现在是等人来拿走的时候。"""
        return pet.tick >= SNIFF + HUFF + EXPLAIN

    def tick(self, pet):
        t = pet.tick
        if t == SNIFF:
            pet.say("picky", 1.8)                      # 才不吃！
        elif t == SNIFF + HUFF:
            pet.say("rutaceae", 2.2)                   # 我只吃芸香科！
        elif self.waiting(pet) and (t - SNIFF - HUFF - EXPLAIN) % NAG == 0:
            pet.say("take_away", 1.6)                  # 拿走！
        if t * TICK_MS / 1000 > REFUSE_WAIT:           # 一直没人管：扭过头去，不理它了
            pet.say("hum", 1.6)
            pet.dir = -pet.dir
            pet.start("idle", random.uniform(3, 6))

    def take_away(self, pet):
        """你把叶子拿走了。"""
        pet.say("better", 2)                           # 这才对嘛
        pet.start("idle", random.uniform(3, 6))

    def frame(self, pet):
        deg, mirrored = world.pose_transform(pet)
        t = pet.tick
        if SNIFF <= t < SNIFF + HUFF:                  # 哼！冒小角，抖一抖
            return "angry", t, QPointF(pet.ax, pet.ay), deg, mirrored
        return "idle", t // self.frame_every, QPointF(pet.ax, pet.ay), deg, mirrored

    def under(self, pet, index):
        return pet.sp.leaves[pet.leaf_kind]["frames"][0]           # 那片没咬过的叶子，一直摆在嘴前面
