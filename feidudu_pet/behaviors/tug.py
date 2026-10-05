"""拉扯：按住往外拉，它死死抓住（不放！）。拉满坚持 TUG_HOLD 秒才松手（哇啊～），变成被拎起来。
没拉下来就松手：弹回原来的地方，哼一声扭一扭。"""
import math

from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QCursor

from . import register
from .base import Behavior
from .. import world
from ..config import TICK_MS, TUG_HOLD, TUG_PULL


@register
class Tug(Behavior):
    name = "tug"
    anim = "tug"
    duration = None

    def enter(self, pet, cursor=None, **kw):
        foot, grip = pet.sp.anims["crawl"].anchor, pet.sp.anims["tug"].anchor
        pet.tug_anchor = world.local_to_world(pet, grip.x() - foot.x(), grip.y() - foot.y())   # 后脚抓着的地方
        pet.saved_pose = (pet.surface, pet.side, pet.on_window, pet.win_edge, pet.dir, pet.ax, pet.ay, pet.win_hwnd)
        pet.tug_hold = 0.0
        pet.tension = 0.0
        pet.say("nope", 60)
        self.pull(pet, cursor, 0)

    def tick(self, pet):
        self.pull(pet, QPointF(QCursor.pos()), TICK_MS / 1000)

    def pull(self, pet, cursor, dt):
        pet.cursor = QPointF(cursor)
        d = pet.cursor - pet.tug_anchor
        pet.tension = min(1.0, math.hypot(d.x(), d.y()) / (TUG_PULL * pet.scale()))
        pet.tug_hold = pet.tug_hold + dt if pet.tension >= 0.9 else max(0.0, pet.tug_hold - dt)
        if pet.tug_hold >= TUG_HOLD:
            pet.say("aah", 1.6)
            pet.start("lifted", cursor=cursor)

    def release(self, pet):
        (pet.surface, pet.side, pet.on_window, pet.win_edge, pet.dir,
         pet.ax, pet.ay, pet.win_hwnd) = pet.saved_pose
        pet.say("hum", 1.4)
        pet.start("wiggle", 1.2, quiet=True)

    def frame(self, pet):
        d = pet.cursor - pet.tug_anchor
        angle = math.degrees(math.atan2(d.y(), d.x()))
        mirrored = math.cos(math.radians(angle)) > 0         # 往右拉就用头朝右的样子
        deg = angle if mirrored else angle - 180
        return self.anim, round(pet.tension * 5), pet.tug_anchor, deg, mirrored
