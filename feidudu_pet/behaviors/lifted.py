"""被拎起来：捏住背，团成松松的 C 字，有点不高兴地扭。松手就吐丝降落。"""
from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QCursor

from . import register
from .base import Behavior
from .. import world


@register
class Lifted(Behavior):
    name = "lifted"
    anim = "lifted"
    duration = None

    def enter(self, pet, cursor=None, **kw):
        pet.surface, pet.on_window, pet.win_edge = "air", False, None
        pet.ax, pet.ay = cursor.x(), cursor.y()
        if pet.bubble != "aah":
            pet.say("hum", 1.4)

    def tick(self, pet):
        pos = QCursor.pos()
        pet.ax, pet.ay = pos.x(), pos.y()

    def follow(self, pet, cursor):
        pet.ax, pet.ay = cursor.x(), cursor.y()

    def release(self, pet):
        pet.bubble = None
        world.emergency_silk(pet)

    def frame(self, pet):
        return self.anim, pet.tick // self.frame_every, QPointF(pet.ax, pet.ay), 0, False
