"""摸摸：鼠标（不按键）在它身上来回划几下，它就舒服得瘫下来，脸红红的（舒服～）。
一停手它就慢慢回过神来；一直摸下去会被摸睡着。
划了几下是 stroke() 数的（pet.feel_strokes 每拍看鼠标是不是在它身上、没按键，是就调它）。"""
import random
import time

from . import register
from .base import Behavior
from .. import world
from ..config import PET_PAUSE, PET_SLEEPY, PET_STROKES, PET_WINDOW, STROKE_LEN

PETTABLE = {"idle", "crawl", "wave", "wiggle", "approach", "look"}     # 这些时候摸它，它会瘫下来


def stroke(pet, pos):
    """鼠标在它身上挪了一下（pos 是屏幕坐标）。顺着身子的方向来回划，每划够 STROKE_LEN 算一下。"""
    last, pet.stroke_last = pet.stroke_last, pos
    if last is None:
        return
    deg, _ = world.pose_transform(pet)
    d = pos.x() - last.x() if deg in (0, 180) else pos.y() - last.y()     # 在墙上就看上下划
    if abs(d) < 0.5:
        return
    sign = 1 if d > 0 else -1
    if sign != pet.stroke_dir:                       # 掉头了：新的一下
        pet.stroke_dir, pet.stroke_run, pet.stroke_counted = sign, 0.0, False
    pet.stroke_run += abs(d)
    if pet.stroke_counted or pet.stroke_run < STROKE_LEN * pet.scale():
        return
    pet.stroke_counted = True
    now = time.time()
    pet.strokes = [t for t in pet.strokes if now - t < PET_WINDOW] + [now]
    if pet.state in ("comfy", "sleep"):
        pet.stroked_at = now                         # 还在摸：接着舒服 / 接着睡
    elif pet.state in PETTABLE and len(pet.strokes) >= PET_STROKES:
        pet.start("comfy")


@register
class Comfy(Behavior):
    name = "comfy"
    anim = "comfy"
    frame_every = 3
    duration = None

    def enter(self, pet, **kw):
        pet.say("comfy", 2)
        pet.petted_since = pet.stroked_at = time.time()

    def tick(self, pet):
        now = time.time()
        if now - pet.stroked_at > PET_PAUSE:         # 不摸了
            return pet.start("idle", random.uniform(3, 6))
        if now - pet.petted_since > PET_SLEEPY:      # 摸得太舒服，睡着了
            pet.start("sleep", random.uniform(40, 90))
            return pet.say("sleepy", 2)
        if pet.tick % 45 == 0:
            pet.say("comfy", 2)
