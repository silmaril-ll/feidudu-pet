"""吃叶子：一口一口啃，吃完长胖一点点。
右键「喂一片叶子」吃的是平常的柑橘叶；小卖部抽到的神秘叶子也走这里（leaf= 叶子的名字，见 art-source/items.js）。
吃进去的过一会儿变成便便（behaviors/frass.py），吃饱了还会犯困（behaviors/sleep.py），
特别的叶子吃完还有特别效果（effects.py）。
一顿一顿地吃：FULL_BOUT 分钟里连吃 FULL_AFTER 片就饱了，FULL_MINUTES 分钟里吃不下（存在存档里，关掉再开也还饱着）。"""
import random
import time

from PyQt6.QtCore import QTimer

from . import register
from .base import Behavior
from ..lang import tr
from .. import effects
from ..config import FRASS_PER_LEAF, FULL_AFTER, PARTY_EVERY, FULL_BOUT, FULL_MINUTES, GROW_PER_LEAF, MAX_GROWTH
from ..save import write_save

BITES, CHEWS = 4, 6          # 咬 4 口（叶子画面 4 个样子），每口嚼 6 下（munch 画面 6 帧）


def is_full(pet):
    return time.time() < pet.save.get("full_until", 0)


def full_minutes_left(pet):
    return max(1, round((pet.save.get("full_until", 0) - time.time()) / 60))


def refuse_reason(pet):
    """现在能不能喂：能就返回 None；不能就返回它要冒的泡泡（睡着 / 吃饱了 / 在墙上吊着这些地方吃不了）。"""
    if pet.state == "sleep":
        return "asleep"                              # 嘘～睡着呢
    if is_full(pet):
        return "stuffed"
    if pet.surface != "floor" or pet.busy() or pet.state in ("munch", "nibble", "snake", "refuse"):
        return "dots"
    return None


def record_meal(pet):
    """记下这一顿；一小段时间里吃够了就“吃饱了”，返回 True。"""
    now = time.time()
    meals = [t for t in pet.save.get("meals", []) if now - t < FULL_BOUT * 60] + [now]
    full = len(meals) >= FULL_AFTER
    if full:
        pet.save["full_until"] = now + FULL_MINUTES * 60
        meals = []
    pet.save["meals"] = meals
    return full


def after_meal(pet, leaf, full):
    """吃完一片以后：歇一会儿；特别的叶子有特别效果，普通的叶子就“好吃！”再打个嗝（吃饱了就是“好撑～”）。"""
    pet.start("idle", random.uniform(4, 8))
    if not effects.apply(pet, leaf):
        pet.say("full" if full else "yum", 1.8)
        QTimer.singleShot(2200, lambda: pet.say("burp", 1.6) if pet.state == "idle" else None)


@register
class Munch(Behavior):
    name = "munch"
    anim = "munch"
    frame_every = 2
    duration = None
    menu_order = 10

    def enter(self, pet, leaf="citrus", **kw):
        pet.leaf_kind = leaf if leaf in pet.sp.leaves else "citrus"
        if pet.leaf_kind != "citrus":
            pet.say("leaf_" + pet.leaf_kind, 2.2)          # 抽到什么了！

    def tick(self, pet):
        if pet.tick >= BITES * CHEWS * self.frame_every:
            pet.save["leaves"] = pet.save.get("leaves", 0) + 1
            pet.save["growth"] = min(MAX_GROWTH, pet.save.get("growth", 1.0) + GROW_PER_LEAF)
            pet.save["gut"] = pet.save.get("gut", 0) + FRASS_PER_LEAF
            pet.fed_at = time.time()
            full = record_meal(pet)
            write_save(pet.save)
            pet.apply_size()
            leaf = pet.sp.leaves[pet.leaf_kind]
            if pet.save["leaves"] % PARTY_EVERY == 0:      # 吃满一百片：先放礼花庆祝，放完再接着下面的
                return pet.start("party", count=pet.save["leaves"], leaf=leaf, full=full)
            after_meal(pet, leaf, full)

    def under(self, pet, index):
        return pet.sp.leaves[pet.leaf_kind]["frames"][min(index // CHEWS, BITES - 1)]

    def menu_items(self, pet):
        if is_full(pet):
            return [(tr(f"喂一片叶子（吃饱了，还要 {full_minutes_left(pet)} 分钟）",
                        f"Feed a leaf (full — {full_minutes_left(pet)} more min)"), pet.feed)]
        return [(tr(f"喂一片叶子（已经吃了 {pet.save.get('leaves', 0)} 片）",
                    f"Feed a leaf ({pet.save.get('leaves', 0)} eaten so far)"), pet.feed)]
