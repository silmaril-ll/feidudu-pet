"""追逗虫棒：拿着逗虫棒的时候（toys.py），它盯着那片叶子——叶子在前面远了就爬过去，近了就抬起前半身、头对着叶子；
叶子在它嘴边停一小会儿，就一口咬住，开始拔河（tussle.py）。拔河它赢了（won）：先趴着把抢到的叶子嚼完
（munch 的帧，垫着 wand_leaf 那片嫩叶一口一口变小，chase_chew_until），“好吃！”，再开心地扭一扭（chase_happy_until）；
叶子长回来之前（HandToy.bare）不追光秃秃的线。只是演一下，不算吃了一片。
抬身子用的是看鼠标（look.py）的那 9 帧，爬用 crawl 的帧。"""
import math
import random
import time

from PyQt6.QtCore import QPointF

from . import register
from .base import Behavior
from .look import FRAMES, HEAD, REACH, TOP, hinge
from .. import world
from ..config import CRAWL_SPEED

SNATCH = 0.5          # 叶子在嘴边停多少秒就咬住
CHEW = 2.6            # 抢到的叶子趴着嚼多久（嚼完“好吃！”）
WIGGLE = 1.0          # 嚼完开心地扭多久
REGROW = 4.0          # 抢走以后线头上的叶子几秒长回来（比嚼加扭长一点）


@register
class Chase(Behavior):
    name = "chase"
    anim = "look"
    duration = None

    def enter(self, pet, **kw):
        pet.look_idx = 0.0
        pet.chase_crawling = False
        pet.chase_near = 0.0
        pet.chase_turned = 0.0
        pet.chase_happy_until = 0.0
        pet.chase_chew_until = 0.0

    def tick(self, pet):
        if pet.toy != "wand" or pet.surface != "floor":
            return pet.start("idle", random.uniform(2, 4))
        now, s = time.time(), pet.scale()
        if pet.chase_chew_until:
            if now < pet.chase_chew_until:                               # 刚抢到：趴着嚼
                return
            pet.chase_chew_until = 0.0
            pet.say("yum", 1.4)
        if now < pet.chase_happy_until:                                  # 嚼完：开心地扭一扭，扭完接着追
            return
        if pet.hand.bare():                                              # 叶子被抢走了，线头上什么都没有：歇着等它长回来
            pet.chase_crawling = False
            pet.chase_near = 0.0
            pet.look_idx += (0 - pet.look_idx) * 0.35
            return
        leaf = pet.hand.tip()
        forward = (leaf.x() - pet.ax) * pet.dir
        if forward < -25 * s and now - pet.chase_turned > 0.6:          # 跑到身后了：转身
            pet.dir, pet.chase_turned = -pet.dir, now
            return
        ahead = forward + HEAD[0] * s                                   # 叶子在头前面多远（HEAD[0] 是负的）
        pet.chase_crawling = ahead > 70 * s
        if pet.chase_crawling:                                          # 远了：爬过去（比平常快一点）
            self.crawl(pet, CRAWL_SPEED * 1.6 * s)
            pet.look_idx = 0.0
            pet.chase_near = 0.0
            return
        h = hinge(pet)
        up, fwd = h.y() - leaf.y(), (leaf.x() - h.x()) * pet.dir
        target = min(max(math.atan2(up, max(fwd, 1)), 0), TOP) / TOP * (FRAMES - 1)
        pet.look_idx += (target - pet.look_idx) * 0.35
        near = math.hypot(leaf.x() - h.x(), leaf.y() - h.y()) < (REACH + 20) * s and up > -20 * s
        if not near or pet.hand.bare() or now < pet.chase_bite_after:
            pet.chase_near = 0.0
            return
        pet.chase_near += 0.09
        if pet.chase_near >= SNATCH:                                    # 啊呜！咬住了，拔河
            pet.start("tussle")

    @staticmethod
    def won(pet):
        """拔河赢了（tussle.py 调）：叼着叶子回来，先嚼、再扭，线头上的叶子过一会儿长回来。"""
        now = time.time()
        pet.hand.bare_until = now + REGROW
        pet.start("chase")
        pet.chase_chew_until = now + CHEW
        pet.chase_happy_until = now + CHEW + WIGGLE
        pet.say("got_it", 1.8)

    def chewing(self, pet):
        return time.time() < pet.chase_chew_until

    def under(self, pet, index):
        if not self.chewing(pet):
            return None
        done = 1 - (pet.chase_chew_until - time.time()) / CHEW            # 嚼到哪了：0 → 1
        return pet.sp.leaves["wand_leaf"]["frames"][min(int(done * 4), 3)]

    def crawl(self, pet, speed):
        """沿着脚下的面往前爬，到边上就停（不爬墙、不吐丝，专心追叶子）。"""
        half = pet.sp.half * pet.scale()
        if pet.on_window and pet.win is not None:
            lo, hi = pet.win.left() + half * 0.6, pet.win.right() - half * 0.6
        else:
            a = world.area()
            lo, hi = a.left() + half, a.right() + 1 - half
        pet.ax = min(max(pet.ax + speed * pet.dir, lo), hi)

    def frame(self, pet):
        deg, mirrored = world.pose_transform(pet)
        if self.chewing(pet):
            return "munch", pet.tick // 2, QPointF(pet.ax, pet.ay), deg, mirrored
        if time.time() < pet.chase_happy_until:
            return "wiggle", pet.tick, QPointF(pet.ax, pet.ay), deg, mirrored
        if pet.chase_crawling:
            return "crawl", pet.tick, QPointF(pet.ax, pet.ay), deg, mirrored
        return self.anim, round(pet.look_idx), QPointF(pet.ax, pet.ay), deg, mirrored
