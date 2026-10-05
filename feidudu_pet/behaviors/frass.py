"""拉便便：吃进去的叶子过一会儿变成小颗粒。尾巴稍微抬一下，“噗”，一颗掉下去，落到任务栏上。
在窗口上沿不拉（不弄脏你正在用的窗口）。"""
import random

from PyQt6.QtCore import QPointF

from . import register
from .base import Behavior
from .. import world
from ..save import write_save

SEQ = [0, 1, 2, 3, 3, 3, 3, 3, 2, 1, 0]      # strain 画面：抬尾巴、停住、放下
DROP_AT = 4                                    # 停住的时候掉下来


@register
class Frass(Behavior):
    name = "frass"
    anim = "strain"
    frame_every = 2
    duration = None
    menu_order = 15

    def weight_for(self, pet):
        if pet.save.get("gut", 0) <= 0 or pet.surface not in ("floor", "wall", "ceiling"):
            return 0
        if pet.on_window and pet.win_edge == "top":
            return 0
        return 0.5

    def tick(self, pet):
        step = pet.tick // self.frame_every
        if step == DROP_AT and pet.tick % self.frame_every == 0:
            self.drop(pet)
        if step >= len(SEQ):
            pet.start("idle", random.uniform(2, 5))

    def drop(self, pet):
        crawl = pet.sp.anims["crawl"]
        tail = crawl.bbox.right() - crawl.anchor.x() - 12          # 尾巴尖往里一点
        pet.drop_frass(world.local_to_world(pet, tail, -12))
        pet.save["gut"] = max(0, pet.save.get("gut", 0) - 1)
        write_save(pet.save)
        if random.random() < 0.4:
            pet.say("pu", 1.2)

    def frame(self, pet):
        deg, mirrored = world.pose_transform(pet)
        i = SEQ[min(pet.tick // self.frame_every, len(SEQ) - 1)]
        return self.anim, i, QPointF(pet.ax, pet.ay), deg, mirrored

    def menu_items(self, pet):
        return [(f"把便便都捡起来（花肥攒了 {pet.save.get('frass', 0)} 颗）", pet.pick_all_frass)]
