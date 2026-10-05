"""
肥嘟嘟本体：一个透明、不抢焦点、永远在最上面的小窗口。

它只管四件事：记住自己在哪（位置和所在的面）、每一拍让当前动作走一步、把画面画出来、接鼠标和右键菜单。
具体每种动作做什么，都在 behaviors/ 文件夹里；面怎么爬、怎么转角，在 world.py。

位置用一个“支点”来记（屏幕坐标）：
  在地板/窗口上沿/天花板/墙上：支点是脚底中间，贴着那个面；
  吊在丝上：支点是嘴巴；被拎着：支点是捏住的地方；被拉扯：支点是后脚。
画的时候把这一帧的支点对准它，再按动作给的角度旋转/镜像。
"""
import math
import random
import time

from PyQt6.QtCore import QPoint, QPointF, QRectF, Qt, QTimer
from PyQt6.QtGui import QColor, QCursor, QGuiApplication, QPainter, QTransform
from PyQt6.QtWidgets import QApplication, QWidget

from . import clock, effects, shop, world
from .behaviors import REGISTRY, pick_next
from .behaviors.cling import hold_on
from .behaviors.comfy import stroke
from .behaviors.look import notice
from .behaviors.munch import refuse_reason
from .behaviors.peek import check_in
from .behaviors.sleep import nod_off, welcome
from .config import (BUBBLE_MIN, BUBBLE_ROOM, DEFAULT_SIZE, FRASS_ON_SCREEN, GAME_CHECK_MS, GAME_TITLES, GAMES,
                     POKE_WIGGLE, REACH,
                     SCENTS, SIZE_OPTIONS, SNAKE_POKES, SNAKE_WINDOW, SPARKLES, TICK_MS, WINDOW_CHECK_TICKS)
from .disguise import ImeBar, default_spot
from .lang import tr
from .menu import add_submenu, crayon_menu
from .pellets import Pellet
from .save import load_save, write_save
from .senses import Senses
from .silk import SilkThread
from .silk_trail import SilkTrail
from .win32 import ActiveWindow, foreground_app, no_activate


class FeiDuDu(QWidget):
    def __init__(self, sprites, window_source=None):
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
                         | Qt.WindowType.Tool | Qt.WindowType.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setWindowTitle(tr("肥嘟嘟", "FeiDuDu"))

        self.sp = sprites
        self.save = load_save()
        self.silk = SilkThread()
        self.silk_trail = SilkTrail()
        self.pellets = []               # 地上还没捡的便便
        self.ime = ImeBar(sprites.skin, self.undisguise, self.remember_ime_spot)    # 伪装用的输入法皮肤
        self.tray = None                # 托盘图标（app.py 放进来），伪装时藏起来
        self.windows = window_source or ActiveWindow().rect      # 返回 (窗口编号, 矩形)
        self.senses = Senses()          # 鼠标在哪、多快，人多久没碰电脑（senses.py）

        # 所在的面（意思见 world.py 开头）
        self.surface = "floor"
        self.side = "L"                 # 在墙上时：墙在它哪一边
        self.on_window = False
        self.win_edge = None
        self.dir = -1                   # 沿着面往哪走：地板上 -1 左 +1 右；墙上 -1 上 +1 下
        self.ax = 0.0                   # 支点位置
        self.ay = 0.0

        # 动作
        self.state = "idle"
        self.behavior = REGISTRY["idle"]
        self.state_until = 0.0
        self.tick = 0
        self.goal_window = False        # 这会儿想去窗口上
        self.goal_until = 0.0

        # 各个动作用到的小记录
        self.silk_top = QPointF()
        self.silk_fast = False
        self.silk_pause = 0
        self.saved_pose = None
        self.tug_anchor = QPointF()
        self.tug_hold = 0.0
        self.tension = 0.0
        self.cursor = QPointF()
        self.waved = False              # 刚在边上探过路
        self.wave_seq = []
        self.wave_edge = False
        self.fed_at = 0.0               # 上次吃完叶子的时间
        self.leaf_kind = "citrus"       # 正在吃哪种叶子
        self.fly_minutes = 10           # 梦蝶：要飞多久
        self.fly_until = 0.0
        self.fly_vx = 0.0
        self.fly_target = QPointF()
        self.pokes = []                 # 最近几次戳它的时间（戳多了会装蛇）
        self.under_rect = None          # 垫在身体下面的那一层（比如枫叶）在窗口里的位置
        self._menu = None               # 正开着的右键菜单
        self.away_nap = False           # 人走开了，睡着等人回来
        self.win_seen_at = 0.0          # 上次看活动窗口的时间
        self.win_velocity = (0.0, 0.0)  # 脚下的窗口挪得多快（像素/秒）
        self.cling_still = 0.0          # 抓着窗口的时候：窗口上次还在动的时间
        self.cling_turns = []
        self.cling_last = (0.0, 0.0)
        self.stroke_last = None         # 摸摸：鼠标上一次在哪、往哪划、划了多远
        self.stroke_dir = 0
        self.stroke_run = 0.0
        self.stroke_counted = False
        self.strokes = []               # 最近几下摸的时间
        self.stroked_at = 0.0
        self._hit_images = {}           # 看鼠标在不在身子上用的画面（按需要转成 QImage 存着）
        self.petted_since = 0.0
        self.look_next = 0.0            # 看鼠标：什么时候才可以再看
        self.look_rolled = None         # 这次鼠标停下来已经掷过要不要看了
        self.look_until = 0.0
        self.look_idx = 0.0             # 现在抬到第几帧（慢慢转过去，是小数）
        self.look_since = 0.0
        self.look_turned = 0.0
        self.look_reached = False
        self.approach_then = None
        self.approach_hurry = True
        self.peek_seq = []
        self.rest_next = 0.0            # 提醒你歇一下：下次最早什么时候

        # 活动窗口
        self.win_hwnd = None
        self.win = None
        self.win_prev = None
        self.active_hwnd = None         # 现在的活动窗口（不一定是它脚下那个）

        # 泡泡、鼠标
        self.bubble = None
        self.bubble_until = 0.0
        self.press_at = None
        self.pressing = False
        self._click_pending = False

        self.apply_size()
        a = world.area()
        self.ax, self.ay = a.right() - 200, a.bottom() + 1
        self.greet()
        self.start("idle", 2.0)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.step)
        self.timer.start(TICK_MS)

        # 暂停（安静一会儿）：None = 没暂停，"manual" = 你让它睡的，"game" = 打游戏它自己去睡的
        self.paused = None
        self._games = {name.lower() for name in GAMES}
        self.game_timer = QTimer(self)
        self.game_timer.timeout.connect(self.watch_games)
        if GAMES or GAME_TITLES:                                     # 没写游戏就不用看
            self.game_timer.start(GAME_CHECK_MS)

    # ---------- 尺寸

    def scale(self):
        return self.save.get("size", DEFAULT_SIZE) * self.save.get("growth", 1.0)

    def apply_size(self):
        side = int(2 * REACH * self.scale()) + 20
        self.setFixedSize(side, side + BUBBLE_ROOM)

    def pivot(self):
        """窗口里放支点的位置。"""
        return QPointF(self.width() / 2, BUBBLE_ROOM + (self.height() - BUBBLE_ROOM) / 2)

    def set_size(self, value):
        self.save["size"] = value
        write_save(self.save)
        self.apply_size()
        self.sync()

    # ---------- 动作

    def start(self, name, seconds=None, **kw):
        """换成另一个动作。seconds 是做多久（到时间就随机挑下一个）；kw 会传给动作的 enter。"""
        self.behavior.exit(self)
        self.state = name
        self.behavior = REGISTRY[name]
        self.tick = 0
        self.state_until = time.time() + seconds if seconds else 0.0
        self.behavior.enter(self, **kw)
        self.sync()

    def say(self, name, seconds=2.0):
        self.bubble = name
        self.bubble_until = time.time() + seconds

    def step(self):
        now = time.time()
        self.tick += 1
        world.track_screen(self)
        if self.senses.update():                      # 人回来了
            welcome(self)
        elif self.senses.away:                        # 人走开了：找地方睡
            nod_off(self)
        else:
            notice(self)                              # 鼠标停在旁边：看看它
            self.feel_strokes()                       # 鼠标在身上划：摸摸
            check_in(self)                            # 忙完啦？歇一下？
        if self.tick % WINDOW_CHECK_TICKS == 0 or self.state == "cling":     # 抓着窗口的时候每拍都看
            world.check_window(self)
            hold_on(self)
            self.silk_trail.show(self)
        for pellet in self.pellets:
            pellet.fall()
        if self.goal_window and now > self.goal_until:
            self.goal_window = False
        behavior = self.behavior
        behavior.tick(self)
        if self.behavior is behavior and self.state_until and now > self.state_until:
            pick_next(self)
        if self.bubble and now > self.bubble_until:
            self.bubble = None
        self.sync()

    # ---------- 便便

    def drop_frass(self, point):
        self.pellets.append(Pellet(self.sp.frass, point, max(self.scale(), 0.7), self.pick_frass))
        if len(self.pellets) > FRASS_ON_SCREEN:            # 太多了，最早那颗化进土里
            self.pellets.pop(0).close()

    def pick_frass(self, pellet, save=True):
        """捡起一颗，攒着当花肥。"""
        self.pellets.remove(pellet)
        pellet.close()
        self.save["frass"] = self.save.get("frass", 0) + 1
        if save:
            write_save(self.save)

    def pick_all_frass(self, *_):
        for pellet in list(self.pellets):
            self.pick_frass(pellet, save=False)
        write_save(self.save)

    # ---------- 伪装成输入法

    def disguise(self, *_):
        """藏起来：变成一条输入法状态栏。一切停下，丝、丝垫、便便、托盘图标都藏好。"""
        if self.ime.isVisible() or self.paused:
            return
        self.timer.stop()
        self.bubble = None
        for w in (self, self.silk, self.silk_trail.floor_mat, self.silk_trail.window_mat, *self.pellets):
            w.hide()
        if self.tray:
            self.tray.hide()
        spot = self.save.get("ime_pos")
        spot = QPoint(*spot) if spot else None
        if spot is None or QGuiApplication.screenAt(spot) is None:     # 没存过，或者那块屏幕不在了
            spot = default_spot(world.area(), self.ime)
        self.ime.move(spot)
        self.ime.show()

    def undisguise(self, *_):
        """双击输入法的小叶子 / 右键「还原」：肥嘟嘟回来，接着刚才的事做。"""
        if not self.ime.isVisible():
            return
        self.ime.hide()
        for pellet in self.pellets:
            pellet.show()
        if self.tray:
            self.tray.show()
        self.show()
        self.say("back", 2.5)
        self.senses.resume()
        self.timer.start(TICK_MS)
        self.sync()

    # ---------- 安静一会儿（暂停）

    def pause(self, why="manual"):
        """让它去睡：一切停下、全藏起来（伪装的输入法也藏），只留托盘图标。停着的时候不占资源。"""
        if self.paused:
            return
        self.paused = why
        self.timer.stop()
        self.bubble = None
        for w in (self, self.silk, self.silk_trail.floor_mat, self.silk_trail.window_mat, self.ime, *self.pellets):
            w.hide()
        if self.tray:
            self.tray.show()                                         # 托盘图标留着，点它叫它出来
            self.tray.setToolTip(tr("肥嘟嘟在睡觉（单击叫它出来）", "FeiDuDu is asleep (click to wake it)"))

    def unpause(self, *_):
        """叫它出来：接着刚才的事做。"""
        if not self.paused:
            return
        self.paused = None
        for pellet in self.pellets:
            pellet.show()
        if self.tray:
            self.tray.setToolTip(tr("肥嘟嘟", "FeiDuDu"))
        self.show()
        self.say("back", 2.5)
        self.senses.resume()
        self.timer.start(TICK_MS)
        self.sync()

    def toggle_pause(self, *_):
        self.unpause() if self.paused else self.pause()

    def watch_games(self):
        """每 GAME_CHECK_MS 看一眼最前面是什么程序：是 config 里写的游戏就去睡，切走了就出来。
        你自己让它睡的（"manual"）不管，要你自己叫它。"""
        app = foreground_app()
        if app is None:
            return
        exe, title = app
        playing = exe.lower() in self._games or any(word in title for word in GAME_TITLES)
        if playing and not self.paused:
            self.pause("game")
        elif not playing and self.paused == "game":
            self.unpause()

    def remember_ime_spot(self, pos):
        self.save["ime_pos"] = [pos.x(), pos.y()]
        write_save(self.save)

    # ---------- 右键菜单里的操作

    def busy(self):
        return self.state in ("hang", "lifted", "tug", "pupa", "butterfly", "cling")

    def feed(self, *_):
        """喂一片柑橘叶。睡着了、吃饱了、在墙上吊着的时候不吃（叶子不给出去）。"""
        reason = refuse_reason(self)
        if reason:
            return self.say(reason, 1.8)
        self.start("munch")

    def greet(self, seconds=2.5):
        """按现在几点打招呼：早呀 / 中午好 / 下午好 / 晚上好 / 夜深啦。"""
        self.say(clock.greeting(), seconds)

    def wiggle(self, *_):
        if not self.busy():
            self.start("wiggle", 1.6)

    def poke(self):
        """单击：睡着就被戳醒；平时随机一个反应，多半扭一扭，有时冒出橙色小角。"""
        if self.state == "sleep":
            self.say("dots", 1.6)
            return self.start("idle", 4)
        if self.busy() or self.state == "snake":
            return
        now = time.time()
        self.pokes = [t for t in self.pokes if now - t < SNAKE_WINDOW] + [now]
        if len(self.pokes) >= SNAKE_POKES:                # 戳太多下了：装成小蛇吓唬你
            self.pokes = []
            return self.start("snake")
        if random.random() < POKE_WIGGLE:
            self.start("wiggle", 1.6)
        else:
            self.start("angry", 1.6)

    def back_to_floor(self, *_):
        a = world.area()
        self.surface, self.on_window, self.win_edge = "floor", False, None
        self.ay = a.bottom() + 1
        self.ax = min(max(self.ax, a.left() + 100), a.right() - 100)
        self.start("idle", 3)

    def toggle_break_reminder(self, *_):
        self.save["break_reminder"] = not self.save.get("break_reminder", True)
        write_save(self.save)

    def build_menu(self):
        """右键菜单：只留要人来做的事（喂、捡、买、穿、大小、退出）。
        藏起来 = 双击 / 快捷键，扭一扭 = 单击，睡觉醒来、去窗口回任务栏它自己会（托盘里还有「回到任务栏上」救急）。"""
        menu = crayon_menu()
        items = []
        for b in REGISTRY.values():
            items += [(b.menu_order, text, fn) for text, fn in b.menu_items(self)]
        for _, text, fn in sorted(items, key=lambda i: i[0]):
            menu.addAction(text, fn)
        menu.addSeparator()
        shop.add_to_menu(menu, self)
        menu.addSeparator()
        size_menu = add_submenu(menu, tr("大小", "Size"))
        for zh, en, value in SIZE_OPTIONS:
            action = size_menu.addAction(tr(zh, en), lambda *_, v=value: self.set_size(v))
            action.setCheckable(True)
            action.setChecked(abs(self.save.get("size", DEFAULT_SIZE) - value) < 0.01)
        menu.addAction(tr("安静一会儿（暂停，点托盘图标叫它出来）", "Quiet time (click the tray icon to bring it back)"), self.pause)
        rest = menu.addAction(tr("提醒我歇一歇", "Remind me to take breaks"), self.toggle_break_reminder)
        rest.setCheckable(True)
        rest.setChecked(self.save.get("break_reminder", True))
        menu.addAction(tr("让它去睡（退出）", "Put it to bed (quit)"), QApplication.instance().quit)
        return menu

    # ---------- 鼠标

    def mousePressEvent(self, event):
        if self.state in ("pupa", "butterfly"):               # 在做梦，点不到也拎不起来
            return
        if self.state == "refuse":                            # 挑食的时候：点到那片叶子就拿走，点它本身它只会说“拿走！”
            if event.button() == Qt.MouseButton.LeftButton and self.behavior.waiting(self):
                if self.under_rect is not None and self.under_rect.contains(event.position()):
                    self.behavior.take_away(self)
                else:
                    self.say("take_away", 1.4)
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self.press_at = event.globalPosition()
            self.pressing = False
            if self.state == "hang":                          # 吊着的时候一抓就拎起来
                self.pressing = True
                self.start("lifted", cursor=event.globalPosition())

    def feel_strokes(self):
        """摸摸：每拍看鼠标是不是正停在它身上（没按键），是就交给 comfy.stroke 数划了几下。
        不靠窗口收鼠标移动的消息（Windows 不一定发给不抢焦点的窗口），自己每拍去看鼠标在哪。"""
        cursor = self.senses.cursor
        if self.senses.pressed or self.press_at is not None or not self.isVisible() or not self.touches(cursor):
            self.stroke_last = None                           # 不在身上：下次重新开始数
            return
        stroke(self, cursor)

    def touches(self, point):
        """屏幕上这个点是不是正好在它画出来的身子上（看这一帧画面在那里透不透明）。"""
        name, index, _, deg, mirrored = self.behavior.frame(self)
        anim = self.sp.anims[name]
        index %= len(anim.frames)
        inverse, ok = self.paint_transform(anim, deg, mirrored).inverted()
        if not ok:
            return False
        local = inverse.map(QPointF(point) - QPointF(self.pos()))
        image = self._hit_images.get((name, index))
        if image is None:
            image = self._hit_images[(name, index)] = anim.frames[index].toImage()
        r = self.sp.ratio
        x, y = int(local.x() * r), int(local.y() * r)
        return image.valid(x, y) and image.pixelColor(x, y).alpha() > 40

    def paint_transform(self, anim, deg, mirrored):
        """画面坐标 → 窗口里的坐标：把这一帧的支点放到 pivot，再转、镜像、缩放。"""
        s = self.scale()
        t = QTransform()
        t.translate(self.pivot().x(), self.pivot().y())
        t.rotate(deg)
        t.scale(-s if mirrored else s, s)
        t.translate(-anim.anchor.x(), -anim.anchor.y())
        return t

    def mouseMoveEvent(self, event):
        if self.press_at is None:
            return
        moved = event.globalPosition() - self.press_at
        if not self.pressing and abs(moved.x()) + abs(moved.y()) > 6:
            self.pressing = True
            self.start("tug", cursor=event.globalPosition())
        elif self.state == "tug":
            self.behavior.pull(self, event.globalPosition(), 0)
        elif self.state == "lifted":
            self.behavior.follow(self, event.globalPosition())
            self.sync()

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton or self.press_at is None:
            return
        self.press_at = None
        if self.pressing:
            self.pressing = False
            if self.state in ("tug", "lifted"):
                self.behavior.release(self)
        else:
            self._click_pending = True
            QTimer.singleShot(220, self._single_click)        # 等一下，看是不是双击

    def _single_click(self):
        if self._click_pending:
            self._click_pending = False
            self.poke()

    def mouseDoubleClickEvent(self, event):
        self._click_pending = False
        self.disguise()                                   # 双击：马上伪装成输入法（要快）

    def contextMenuEvent(self, event):
        """右键菜单：同时只开一个；开着的时候留着它的引用，关了再放掉（免得菜单还在用就被回收）。"""
        if self._menu is not None:
            return
        self._menu = self.build_menu()
        try:
            self._menu.exec(QCursor.pos())
        finally:
            self._menu.deleteLater()
            self._menu = None

    # ---------- 画

    def sync(self):
        """把窗口挪到支点在的地方，顺便更新那根丝。"""
        _, _, anchor_world, _, _ = self.behavior.frame(self)
        p = self.pivot()
        self.move(int(anchor_world.x() - p.x()), int(anchor_world.y() - p.y()))
        if hasattr(self.behavior, "silk_line"):
            self.silk.set_line(*self.behavior.silk_line(self))
        elif self.silk.isVisible():
            self.silk.hide()
        self.update()

    def paintEvent(self, event):
        name, index, _, deg, mirrored = self.behavior.frame(self)
        anim = self.sp.anims[name]
        frame = anim.frames[index % len(anim.frames)]
        s = self.scale()

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        t = self.paint_transform(anim, deg, mirrored)
        painter.setTransform(t)
        if self.behavior.on_ground and self.surface == "floor":     # 地上的小影子
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(40, 50, 30, 45))
            painter.drawEllipse(QRectF(anim.anchor.x() - 70, anim.anchor.y() - 3, 140, 9))
        under = self.behavior.under(self, index)                    # 比如正在吃的叶子：(画面, 放在哪)
        self.under_rect = None
        if under is not None:
            painter.drawPixmap(under[1], under[0])
            pix, at = under                                         # 记下叶子在窗口里的位置（点它就拿走，见 mousePressEvent）
            self.under_rect = t.mapRect(QRectF(at.x(), at.y(), pix.width() / pix.devicePixelRatio(),
                                               pix.height() / pix.devicePixelRatio()))
        painter.drawPixmap(QPointF(0, 0), frame)
        layer = shop.wearing_layer(self, name)                      # 戴着的饰品
        if layer:
            pixmap, at = layer[index % len(layer)]
            painter.drawPixmap(at, pixmap)
        if effects.active(self, "sparkle_until"):                   # 金叶子：小星星
            self.draw_aura(painter, t.mapRect(anim.bbox), self.sp.sparkles, SPARKLES)
        if effects.active(self, "scent_until"):                     # 芸香叶：一缕缕往上飘的香味
            self.draw_aura(painter, t.mapRect(anim.bbox), self.sp.scents, SCENTS, rise=24)

        if self.bubble:
            # 泡泡不转、不跟着身体缩小，放在身体最高处的正上方
            box = t.mapRect(anim.bbox)
            painter.resetTransform()
            bubble = self.sp.bubbles[self.bubble]
            b = max(s, BUBBLE_MIN)
            bw = bubble.width() / bubble.devicePixelRatio() * b
            tail = bubble.width() / bubble.devicePixelRatio() / 2 + 1      # 泡泡的小尖角在图的正中间
            x = min(max(box.center().x() - tail * b, 0), self.width() - bw)
            y = max(box.top() - 44 * b, 0)
            painter.translate(x, y)
            painter.scale(b, b)
            painter.drawPixmap(QPointF(0, 0), bubble)
        painter.end()

    def draw_aura(self, painter, box, pictures, count, rise=0):
        """身边的小东西（金叶子的星星、芸香叶的香味）：一个一个轮流淡进来又淡出去，每次换个地方；
        rise 是淡出去的时候往上飘多远。"""
        painter.save()
        painter.resetTransform()
        for k in range(count):
            phase = (self.tick / 14 + k / count) % 1.0
            spot = int(self.tick / 14 + k / count)                   # 每闪完一次换个地方
            rnd = random.Random(spot * 31 + k)
            pic = pictures[rnd.randrange(len(pictures))]
            x = box.left() + rnd.uniform(-0.1, 1.1) * box.width()
            y = box.top() + rnd.uniform(-0.25, 0.9) * box.height() - rise * phase
            painter.setOpacity(math.sin(phase * math.pi))
            w = pic.width() / pic.devicePixelRatio()
            h = pic.height() / pic.devicePixelRatio()
            painter.drawPixmap(QPointF(x - w / 2, y - h / 2), pic)
        painter.restore()

    def showEvent(self, event):
        no_activate(self)
        super().showEvent(event)
