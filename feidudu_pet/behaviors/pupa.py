"""梦蝶（一）：吃了梦蝶叶，困了，就地变成一个小小的蛹（带蛹：腰上一圈丝），轻轻晃几下，然后变成蝴蝶。"""
from . import register
from .base import Behavior
from ..config import PUPA_SECONDS, TICK_MS


@register
class Pupa(Behavior):
    name = "pupa"
    anim = "pupa"
    frame_every = 3
    duration = None

    def enter(self, pet, minutes=10, **kw):
        pet.fly_minutes = minutes

    def tick(self, pet):
        if pet.tick * TICK_MS / 1000 >= PUPA_SECONDS:
            pet.start("butterfly", minutes=pet.fly_minutes)
