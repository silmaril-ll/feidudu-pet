"""窗口被拖着跑：它趴在窗口上沿/侧边，一下子被拽走，赶紧压低身子死死抓住（哇啊～）。
窗口停下来一会儿，它松口气（呼～）；被来回甩得太厉害，就被甩下来，吐丝降落。
窗口动得多快是 world.check_window 量的（pet.win_velocity），抓着的时候每一拍都量。"""
import math
import random
import time

from PyQt6.QtCore import QPointF

from . import register
from .base import Behavior
from ..config import CLING_CALM, CLING_SPEED, FLING_SHAKES, FLING_SPEED, FLING_WINDOW

# 这些时候被拖走才会抓紧；吃东西、挑食、吊着、被拎着这些时候就不管它
CLING_FROM = {"idle", "crawl", "wave", "wiggle", "angry", "sleep", "comfy", "approach", "snake", "look", "peek", "chase"}


def hold_on(pet):
    """刚看完窗口（world.check_window）：脚下的窗口被拖得飞快，就赶紧抓住。"""
    if pet.on_window and pet.state in CLING_FROM and math.hypot(*pet.win_velocity) > CLING_SPEED:
        pet.start("cling")


@register
class Cling(Behavior):
    name = "cling"
    anim = "cling"
    duration = None

    def enter(self, pet, **kw):
        pet.say("aah", 1.6)
        pet.cling_still = time.time()
        pet.cling_turns = []                         # 窗口快速掉头的时间
        pet.cling_last = (0.0, 0.0)

    def tick(self, pet):
        now = time.time()
        vx, vy = pet.win_velocity
        if math.hypot(vx, vy) > 60:
            pet.cling_still = now
        # 来回甩：快速地往反方向走，就算掉一次头
        lx, ly = pet.cling_last
        for v, last in ((vx, lx), (vy, ly)):
            if abs(v) > FLING_SPEED and abs(last) > FLING_SPEED and v * last < 0:
                pet.cling_turns.append(now)
        if abs(vx) > FLING_SPEED or abs(vy) > FLING_SPEED:
            pet.cling_last = (vx if abs(vx) > FLING_SPEED else lx, vy if abs(vy) > FLING_SPEED else ly)
        pet.cling_turns = [t for t in pet.cling_turns if now - t < FLING_WINDOW]
        if len(pet.cling_turns) >= FLING_SHAKES:
            return fling(pet)
        if now - pet.cling_still > CLING_CALM:
            pet.say("phew", 1.6)
            pet.start("idle", random.uniform(2, 4))


def fling(pet):
    """被甩下来了：从抓着的地方往外掉，丝的一头还粘在窗口边上，顺着丝垂到下面去（不会又落回这个窗口上）。"""
    s = pet.scale()
    if pet.win_edge == "left":
        top = QPointF(pet.ax - 14 * s, pet.ay)
    elif pet.win_edge == "right":
        top = QPointF(pet.ax + 14 * s, pet.ay)
    else:
        top = QPointF(pet.ax, pet.ay + 2)          # 从上沿翻下去，挂在窗口前面
    pet.start("hang", top=top, fast=True)
    pet.say("aah", 1.6)
