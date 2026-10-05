"""被戳：冒出橙色小角，哼！（单击时随机的反应之一，见 pet.poke）"""
from . import register
from .base import Behavior


@register
class Angry(Behavior):
    name = "angry"
    anim = "angry"
    duration = (1.6, 1.6)

    def enter(self, pet, **kw):
        pet.say("hum", 1.6)
