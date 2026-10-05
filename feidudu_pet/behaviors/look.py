"""看鼠标：鼠标停在它附近，它好奇地抬起前半身，头跟着鼠标转（画面是 9 个抬起的角度，挑头正对着鼠标的那个）。

什么时候会看（notice，每拍在 pet.step 里调）：在地上闲着或者在爬、鼠标停了 LOOK_STILL 秒、离它不到 LOOK_RADIUS、
没按着鼠标键、不是刚点过、不是停在它身上、上次看完歇够了；每停一次只掷一次 LOOK_CHANCE。
看着的时候：鼠标跑到身后它就转过身；慢慢挪远了它就爬过去接着看（approach 的 then="look"）；
够不着的时候说“够不着～”；鼠标飞快地从它身上划过去，偶尔吓一跳（冒角，更少的时候装蛇）；
看了 LOOK_SPAN 秒、或者鼠标走远了，就没兴趣了。"""
import math
import random
import time

from PyQt6.QtCore import QPointF

from . import register
from .base import Behavior
from .. import world
from ..config import (FLINCH_CHANCE, FLINCH_SPEED, LOOK_CHANCE, LOOK_COOLDOWN, LOOK_RADIUS, LOOK_SPAN,
                      LOOK_STILL)

FRAMES = 9                  # look 画面：第 0 帧是平着，第 8 帧差不多竖起来
TOP = 1.35                  # 第 8 帧抬起的角度（弧度），和 art-source/pet.js 里一样
HINGE = (27.5, -29.7)       # 抬起来的时候绕着弯的地方（相对脚底支点，1 倍大小）
HEAD = (-61, -8.8)          # 平着的时候头在哪
REACH = 95                  # 从弯的地方到头有多长
BODY = (0, -28, 70, 30)     # 身体大概的范围：中间 (x, y)、半宽、半高


def hinge(pet):
    return world.local_to_world(pet, *HINGE)


def on_body(pet, point):
    """这个点在不在它身上（地上的时候）。"""
    s = pet.scale()
    cx, cy, hw, hh = BODY
    return abs(point.x() - pet.ax - cx * s) < hw * s and abs(point.y() - pet.ay - cy * s) < hh * s


def crossed_body(pet, a, b):
    """鼠标这一拍从 a 挪到 b，有没有从它身上划过去。"""
    return any(on_body(pet, a + (b - a) * (k / 10)) for k in range(11))


def notice(pet):
    """看看要不要开始看鼠标。"""
    senses, now = pet.senses, time.time()
    if pet.state not in ("idle", "crawl") or pet.surface != "floor" or now < pet.look_next:
        return
    if senses.still < LOOK_STILL or senses.pressed or now - senses.pressed_at < 2:
        return
    if pet.look_rolled == senses.still_since:           # 这次停下来已经掷过了
        return
    c, h = senses.cursor, hinge(pet)
    if math.hypot(c.x() - h.x(), c.y() - h.y()) > LOOK_RADIUS or c.y() > pet.ay + 10 or on_body(pet, c):
        return
    pet.look_rolled = senses.still_since
    if random.random() < LOOK_CHANCE:
        pet.start("look")
    else:
        pet.look_next = now + 5                         # 这次没理你，过一会儿再说


@register
class Look(Behavior):
    name = "look"
    anim = "look"
    duration = None

    def enter(self, pet, resume=False, **kw):
        now = time.time()
        if not resume:                                  # 爬过去接着看的时候，兴趣不重新算
            pet.look_until = now + random.uniform(*LOOK_SPAN)
            pet.look_reached = False
            if random.random() < 0.3:
                pet.say("hmm", 1.4)
        pet.look_idx = 0.0
        pet.look_since = now
        pet.look_turned = 0.0

    def tick(self, pet):
        now, s = time.time(), pet.scale()
        senses = pet.senses
        c, h = senses.cursor, hinge(pet)
        # 鼠标飞快地从身上划过去：偶尔吓一跳
        if senses.speed > FLINCH_SPEED and crossed_body(pet, senses.prev, c) and random.random() < FLINCH_CHANCE:
            if random.random() < 0.2:
                return pet.start("snake")
            pet.start("angry", 1.2)
            return pet.say("startle", 1.4)
        dist = math.hypot(c.x() - h.x(), c.y() - h.y())
        if now > pet.look_until or dist > LOOK_RADIUS * 1.5 or senses.pressed:
            return pet.start("idle", random.uniform(2, 5))     # 没兴趣了 / 走远了 / 你在忙别的
        forward, up = (c.x() - h.x()) * pet.dir, h.y() - c.y()
        if forward < -30 * s and now - pet.look_turned > 1.0:     # 跑到身后了：转过身来
            pet.dir, pet.look_turned = -pet.dir, now
            return
        ahead = (c.x() - pet.ax) * pet.dir - (-HEAD[0]) * s        # 鼠标在头前面多远
        if ahead > 120 * s and senses.speed < 300 and senses.still > 0.4:     # 慢慢挪远了：爬过去
            return pet.start("approach", 15, quiet=True, then="look")
        target = min(max(math.atan2(up, max(forward, 1)), 0), TOP) / TOP * (FRAMES - 1)
        pet.look_idx += (target - pet.look_idx) * 0.3
        if (not pet.look_reached and now - pet.look_since > 2.5 and senses.still > 1
                and dist > (REACH + 25) * s and up > 0):
            pet.look_reached = True
            pet.say("reach", 1.8)

    def exit(self, pet):
        pet.look_next = time.time() + random.uniform(*LOOK_COOLDOWN)

    def frame(self, pet):
        deg, mirrored = world.pose_transform(pet)
        return self.anim, round(pet.look_idx), QPointF(pet.ax, pet.ay), deg, mirrored
