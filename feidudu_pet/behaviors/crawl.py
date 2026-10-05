"""爬：沿着地板、窗口上沿、墙、天花板爬；到头了怎么办在 world.advance 里。"""
import random

from . import register
from .base import Behavior
from .. import world


@register
class Crawl(Behavior):
    name = "crawl"
    anim = "crawl"
    duration = (6, 18)

    def weight_for(self, pet):
        return {"floor": 0.55, "wall": 0.75, "ceiling": 0.75}.get(pet.surface, 0)

    def enter(self, pet, wander=False, waved=False, **kw):
        pet.waved = waved                            # 刚在边上探过路（见 world.wave_first）
        if wander:                                   # 自己决定出发时，偶尔掉个头
            if random.random() < 0.3:
                pet.dir = -pet.dir
            if pet.goal_window:
                world.aim_for_window(pet)

    def tick(self, pet):
        world.advance(pet)
        if pet.state == "crawl":
            pet.silk_trail.lay(pet)                  # 边爬边在脚下铺丝

    def exit(self, pet):
        pet.silk_trail.stop()
