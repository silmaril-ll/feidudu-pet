"""发呆：原地轻轻呼吸。"""
from . import register
from .base import Behavior


@register
class Idle(Behavior):
    name = "idle"
    anim = "idle"
    frame_every = 2
    duration = (3, 10)

    def weight_for(self, pet):
        return {"floor": 0.35, "wall": 0.25, "ceiling": 0.25}.get(pet.surface, 0)
