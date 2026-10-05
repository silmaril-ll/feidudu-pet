"""特别的叶子吃完有什么效果。叶子在 art-source/items.js 里用 effect: '名字' 选一个，
这里按名字找到对应的函数；新效果就在下面写一个函数，加进 EFFECTS。"""
import random
import time

from .config import EXTRA_FRASS, LONG_NAP
from .save import write_save


def tingly(pet, leaf):
    """花椒叶：嘴巴麻麻的，扭一扭。"""
    pet.say("tingly", 2)
    pet.start("wiggle", 1.8, quiet=True)


def plenty(pet, leaf):
    """柚子叶：吃得好撑，过一会儿比平常多拉几颗便便。"""
    pet.save["gut"] = pet.save.get("gut", 0) + EXTRA_FRASS
    write_save(pet.save)
    pet.say("full", 1.8)


def sparkle(pet, leaf):
    """金叶子：接下来一段时间身边亮晶晶的（关掉再开也还亮着）。"""
    pet.save["sparkle_until"] = max(time.time(), pet.save.get("sparkle_until", 0)) + leaf["minutes"] * 60
    write_save(pet.save)
    pet.say("shiny", 2)


def butterfly(pet, leaf):
    """梦蝶叶：困了……变成蛹，再变成蝴蝶飞一会儿，最后回来说“做了个梦”。（庄周梦蝶）"""
    pet.say("sleepy", 2)
    pet.start("pupa", minutes=leaf["minutes"])


def sour(pet, leaf):
    """柠檬叶：酸！打个哆嗦。"""
    pet.say("sour", 1.8)
    pet.start("wiggle", 1.2, quiet=True)


def scent(pet, leaf):
    """芸香叶：味道很冲，接下来一段时间身边飘着一缕缕香味（关掉再开也还在）。"""
    pet.save["scent_until"] = max(time.time(), pet.save.get("scent_until", 0)) + leaf["minutes"] * 60
    write_save(pet.save)
    pet.say("fragrant", 2)


def long_nap(pet, leaf):
    """黄檗叶：吃完马上犯困，睡一个长长的午觉。"""
    pet.say("sleepy", 2)
    pet.start("sleep", random.uniform(*LONG_NAP) * 60)


EFFECTS = {"tingly": tingly, "plenty": plenty, "sparkle": sparkle, "butterfly": butterfly,
           "sour": sour, "scent": scent, "long_nap": long_nap}


def apply(pet, leaf):
    """吃完以后：有特别效果就做，返回 True；普通叶子返回 False。"""
    fn = EFFECTS.get(leaf.get("effect"))
    if fn is None:
        return False
    fn(pet, leaf)
    return True


def refuses(pet, leaf):
    """吃之前：枫叶这种不是芸香科的，它根本不吃（柑橘凤蝶的毛毛虫只认芸香科）。返回 True 表示不吃。"""
    if leaf.get("effect") != "picky":
        return False
    pet.start("refuse", leaf=leaf["name"])       # 叶子摆出来、闻一闻、才不吃！（behaviors/refuse.py）
    return True


def active(pet, key):
    """金叶子（sparkle_until）、芸香叶（scent_until）的效果还在不在。"""
    return time.time() < pet.save.get(key, 0)
