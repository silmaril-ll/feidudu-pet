"""睡觉：晚上在地板/窗口上沿更爱睡；刚吃完叶子白天也想睡一会儿（吃饱了歇着消化）。假眼睛不会闭上。
人走开了（好几分钟没碰电脑）它也找地方睡，一直睡到人回来：醒了说“你回来啦”，朝鼠标爬过去。"""
import time

from . import register
from .base import Behavior
from ..clock import now
from ..config import NAP_AFTER_MEAL, NIGHT_HOURS


def is_night():
    hour = now().hour
    start, end = NIGHT_HOURS
    return hour >= start or hour < end


@register
class Sleep(Behavior):
    name = "sleep"
    anim = "sleep"
    frame_every = 4
    duration = (40, 90)

    def weight_for(self, pet):
        if pet.surface != "floor":
            return 0
        if is_night():
            return 1.5                                   # 晚上六成的时候会去睡
        if time.time() - pet.fed_at < NAP_AFTER_MEAL:
            return 1.0                                   # 刚吃饱，犯困
        return 0

    def enter(self, pet, away=False, **kw):
        pet.fed_at = 0.0                                 # 睡过这一觉就不困了（一顿饭一个午觉）
        pet.away_nap = away                              # 是不是在等人回来（那就一直睡，不自己醒）
        pet.say("zz", 3)

    def tick(self, pet):
        if pet.tick % 60 == 0:
            pet.say("zz", 2.5)

    def exit(self, pet):
        pet.away_nap = False


def nod_off(pet):
    """人走开了：它在地上闲着的时候就睡下，睡到人回来（已经在睡的就接着睡，不自己醒）。"""
    if pet.state == "sleep":
        pet.away_nap, pet.state_until = True, 0.0
    elif pet.state in ("idle", "crawl", "comfy", "look", "peek") and pet.surface == "floor":
        pet.start("sleep", away=True)


def welcome(pet):
    """人回来了：睡着等人的就醒来，“你回来啦”，朝鼠标爬过去；醒着的就打个招呼。"""
    if pet.state == "sleep" and pet.away_nap:
        return pet.start("approach", 15)
    if not pet.busy() and pet.state not in ("refuse", "snake", "munch"):
        pet.say("welcome", 2.5)
