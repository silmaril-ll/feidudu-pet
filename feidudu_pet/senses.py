"""肥嘟嘟的感觉：每一拍看一眼鼠标在哪、动得多快，人多久没碰电脑了，是不是在忙。
动作们要用就读 pet.senses 里的数，不用自己去问系统。"""
import math
import time

from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QCursor

from . import win32
from .config import AWAY_AFTER, BUSY_CALM, BUSY_LEVEL


class Senses:
    def __init__(self):
        self.cursor = QPointF(QCursor.pos())    # 鼠标在哪（屏幕逻辑像素）
        self.prev = QPointF(self.cursor)        # 上一拍鼠标在哪
        self.speed = 0.0                        # 鼠标动得多快（像素/秒，平滑过）
        self.idle = 0.0                         # 人多久没碰键盘鼠标了（秒）
        self.away = False                       # 人走开了（AWAY_AFTER 秒没碰）
        self.away_since = 0.0
        self.done_busy = 0.0
        self.pressed = False                    # 鼠标键按着（在哪个程序里按都算）
        self.pressed_at = 0.0                   # 上次按着鼠标键的时间
        self.busy = False                       # 在忙：最近一分钟一直有动静（打字、滚网页、挪鼠标都算）
        self.busy_since = 0.0                   # 从什么时候开始忙的
        self._active = set()                    # 最近一分钟里哪几秒有动静
        self._at = time.time()
        self._moved_at = self._at

    def update(self):
        """每一拍调一次。返回 True 表示人刚刚回来（之前走开了，这会儿又碰了电脑）。
        忙完了（之前忙了一阵，这会儿停下来了）记在 self.done_busy：忙了多少秒，没忙完是 0。"""
        now = time.time()
        dt = max(now - self._at, 1e-3)
        pos = QPointF(QCursor.pos())
        moved = math.hypot(pos.x() - self.cursor.x(), pos.y() - self.cursor.y())
        if moved > 0.5:
            self._moved_at = now
        self.speed = 0.6 * self.speed + 0.4 * moved / dt
        self.prev, self.cursor, self._at = self.cursor, pos, now
        self.pressed = win32.buttons_down()
        if self.pressed:
            self.pressed_at = now
        idle = win32.idle_seconds()
        self.idle = idle if idle is not None else now - self._moved_at    # 不是 Windows：只看鼠标
        self._track_busy(now)
        if not self.away and self.idle > AWAY_AFTER:
            self.away, self.away_since = True, now - self.idle
            return False
        if self.away and self.idle < 2:
            self.away = False
            return True
        return False

    def _track_busy(self, now):
        """最近 60 秒里有几秒有动静：超过 BUSY_LEVEL 算在忙，降到 BUSY_CALM 以下算忙完（中间不变，免得一会儿忙一会儿不忙）。"""
        second = int(now)
        if self.idle < 1:
            self._active.add(second)
        self._active = {s for s in self._active if second - s < 60}
        level = len(self._active) / 60
        self.done_busy = 0.0
        if not self.busy and level >= BUSY_LEVEL:
            self.busy, self.busy_since = True, now - 60        # 其实前一分钟就在忙了
        elif self.busy and level <= BUSY_CALM:
            self.busy, self.done_busy = False, now - self.busy_since

    @property
    def still(self):
        """鼠标停了多少秒。"""
        return self._at - self._moved_at

    @property
    def still_since(self):
        """鼠标从什么时候停下来的（每停一次是一个新的数，用来“每停一次只掷一次”）。"""
        return self._moved_at

    def resume(self):
        """伪装了一阵子又回来：别把这段时间算成鼠标一下子飞了很远。"""
        self.cursor = QPointF(QCursor.pos())
        self.prev = QPointF(self.cursor)
        self.speed = 0.0
        self._at = time.time()
