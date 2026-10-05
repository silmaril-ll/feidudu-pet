"""扭扭：原地扭一扭。单击（多半是扭）、点托盘图标、被拉扯没拉下来时都会扭。"""
from . import register
from .base import Behavior


@register
class Wiggle(Behavior):
    name = "wiggle"
    anim = "wiggle"
    duration = (1.6, 1.6)

    def weight_for(self, pet):
        return 0.10 if pet.surface == "floor" else 0

    def enter(self, pet, quiet=False, **kw):
        if not quiet:
            pet.say("niu", 1.6)
