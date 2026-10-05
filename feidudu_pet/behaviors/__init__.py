"""
肥嘟嘟的每一种动作都是这个文件夹里的一个文件。

加一个新动作：
  1. 新建一个 .py 文件，写一个继承 Behavior 的类，用 @register 标一下（照着 idle.py 抄最快）
  2. 需要新画面的话，在 art-source/pet.js 里加一组帧，重新跑 art-source/runpet.py
  不用改别的地方：这里会自动把文件夹里所有文件都读进来。
"""
import importlib
import pkgutil
import random

REGISTRY = {}


def register(cls):
    REGISTRY[cls.name] = cls()
    return cls


def pick_next(pet):
    """一个动作做完了，按各个动作的“想做程度”随机挑下一个。"""
    from .. import world
    from ..config import GOAL_WINDOW_CHANCE
    chance = GOAL_WINDOW_CHANCE * (2 if pet.senses.busy else 1)      # 你在忙的时候更想去窗口上陪你
    if pet.surface == "floor" and not pet.on_window and pet.win and random.random() < chance:
        world.want_window(pet)                  # 想去窗口上玩
    choices = [(b, b.weight_for(pet)) for b in REGISTRY.values()]
    choices = [(b, w) for b, w in choices if w > 0]
    if not choices:
        return pet.start("idle", 3)
    roll = random.uniform(0, sum(w for _, w in choices))
    for b, w in choices:
        roll -= w
        if roll <= 0:
            break
    seconds = random.uniform(*b.duration) if b.duration else None
    pet.start(b.name, seconds, wander=True)


for _module in pkgutil.iter_modules(__path__):
    if _module.name != "base":
        importlib.import_module(f"{__name__}.{_module.name}")
