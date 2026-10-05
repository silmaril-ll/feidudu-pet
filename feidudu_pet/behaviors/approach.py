"""朝鼠标爬过去，到了就停（最多爬几秒，不一定爬得到）。两种时候会做：
  人回来了（sleep.welcome）：醒过来说“你回来啦”，急急地爬（两倍速度）；
  看鼠标的时候鼠标慢慢挪远了（look.py）：安安静静地爬过去，到了接着看（then="look"）。"""
import random

from . import register
from .crawl import Crawl
from .. import world


@register
class Approach(Crawl):
    name = "approach"
    duration = None

    def weight_for(self, pet):
        return 0                                     # 只在别的地方叫它的时候做

    def enter(self, pet, quiet=False, then=None, **kw):
        pet.waved = False
        pet.approach_then = then                     # 到了以后做什么（None = 发呆）
        pet.approach_hurry = not quiet
        if not quiet:
            pet.say("welcome", 2.5)

    def tick(self, pet):
        x = pet.senses.cursor.x()
        if pet.surface != "floor" or abs(x - pet.ax) < 60 * pet.scale():      # 到了（头差不多在鼠标底下）
            if pet.approach_then and pet.surface == "floor":
                return pet.start(pet.approach_then, resume=True)
            return pet.start("idle", random.uniform(3, 6))
        pet.dir = 1 if x > pet.ax else -1
        for _ in range(2 if pet.approach_hurry else 1):     # 急着过去的时候爬快一倍
            world.advance(pet)
            if pet.state != self.name:
                return
        pet.silk_trail.lay(pet)
