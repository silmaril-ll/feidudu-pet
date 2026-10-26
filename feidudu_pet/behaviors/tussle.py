"""和逗虫棒拔河：它咬住叶子（chase.py），后脚抓牢，你把鼠标往外挪，它就被拉长、身子转向你（pull 画面：和被拉扯一样，
但不冒臭角，嘟着嘴使劲），泡泡“嗯——！”。叶子咬在它嘴里，线从树枝头牵到它嘴上（toys.HandToy.mouth）。
线是软的（toys.Line）：离得近线就垂着，算不上拉；线绷直以后再往外拉，线和它的身子一起被拉长。
谁赢：
  你松劲（线几乎不拉）TUSSLE_EASE 秒 → 它赢：把叶子扯下来“抢到了！”，趴着嚼完“好吃！”再扭一扭，线头上的叶子过几秒长回来；
  你拉满坚持 TUSSLE_SLIP 秒 → 叶子从它嘴里滑出去，“哼！”，过一会儿才会再咬；
  拔了太久（GIVE_UP 秒）也算它赢。"""
import math
import time

from . import register
from .base import Behavior
from .chase import Chase
from .. import world
from ..config import TUSSLE_EASE, TUSSLE_PULL, TUSSLE_SLIP

MOUTH = 118          # 后脚到嘴有多远（没拉长的时候，1 倍大小）
STRETCH = 37         # 拉满的时候嘴再往前伸多远
GIVE_UP = 10
TAUT = 1.1           # 线被拉到原来的这么多倍才算绷直（挂着叶子的时候本来就被坠长了一点）


@register
class Tussle(Behavior):
    name = "tussle"
    anim = "pull"
    duration = None

    def enter(self, pet, **kw):
        foot, grip = pet.sp.anims["crawl"].anchor, pet.sp.anims["pull"].anchor
        pet.tussle_grip = world.local_to_world(pet, grip.x() - foot.x(), grip.y() - foot.y())     # 后脚抓着的地方
        pet.tussle_tension = pet.tussle_hold = pet.tussle_ease = 0.0
        pet.tussle_since = time.time()
        pet.say("grr", 1.6)
        self.pull(pet)

    def pull(self, pet):
        """量一量线拉出去多远，把嘴放到对的地方（叶子跟着嘴）。"""
        s = pet.scale()
        end = pet.hand.end()
        dx, dy = end.x() - pet.tussle_grip.x(), end.y() - pet.tussle_grip.y()
        dist = max(math.hypot(dx, dy), 1)
        taut = MOUTH * s + pet.hand.line_length() * TAUT          # 线绷直了才开始算拉（线是软的，近了就垂着）
        pet.tussle_tension = min(1.0, max(0.0, (dist - taut) / (TUSSLE_PULL * s)))
        reach = (MOUTH + STRETCH * pet.tussle_tension) * s
        pet.hand.mouth = pet.tussle_grip + (end - pet.tussle_grip) * (reach / dist)
        pet.tussle_angle = math.degrees(math.atan2(dy, dx))

    def tick(self, pet):
        if pet.toy != "wand":
            return pet.start("idle", 2)
        self.pull(pet)
        now, dt = time.time(), 0.09
        tension = pet.tussle_tension
        pet.tussle_hold = pet.tussle_hold + dt if tension >= 0.9 else max(0.0, pet.tussle_hold - dt)
        pet.tussle_ease = pet.tussle_ease + dt if tension < 0.15 else 0.0
        if pet.tussle_hold >= TUSSLE_SLIP:                  # 你赢了：叶子滑出去
            pet.chase_bite_after = now + 2.0
            pet.start("chase")
            return pet.say("hum", 1.4)
        if pet.tussle_ease >= TUSSLE_EASE or now - pet.tussle_since > GIVE_UP:     # 它赢了：叼回去嚼
            return Chase.won(pet)
        if tension > 0.4 and pet.tick % 25 == 0:
            pet.say("grr", 1.4)

    def exit(self, pet):
        pet.hand.mouth = None                               # 叶子回到树枝上（或者被咬走了）

    def frame(self, pet):
        angle = pet.tussle_angle
        mirrored = math.cos(math.radians(angle)) > 0        # 往右拉就用头朝右的样子
        deg = angle if mirrored else angle - 180
        return self.anim, round(pet.tussle_tension * 5), pet.tussle_grip, deg, mirrored
