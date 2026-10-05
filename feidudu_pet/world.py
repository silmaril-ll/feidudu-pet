"""
屏幕和活动窗口上的“面”：肥嘟嘟站在哪、往哪爬、到头了怎么转弯、从哪儿吐丝下去。

面有四种：
  floor    地板：任务栏上沿，或者活动窗口的上沿（on_window=True, win_edge="top"）
  wall     墙：屏幕左右边，或者活动窗口的左右侧边（win_edge="left"/"right"）
  ceiling  天花板：屏幕顶，倒挂着爬
  air      空中：吊在丝上、被拎着、被拉扯
"""
import math
import random
import time

from PyQt6.QtCore import QPoint, QPointF
from PyQt6.QtGui import QGuiApplication

from .config import CLIMB_SPEED, CRAWL_SPEED, WAVE_CHANCE


_screen = None          # 肥嘟嘟现在在哪块屏幕上（track_screen 每拍更新）


def area():
    """它在的那块屏幕，不含任务栏的区域。"""
    screen = _screen if _screen in QGuiApplication.screens() else QGuiApplication.primaryScreen()
    return screen.availableGeometry()


def track_screen(pet):
    """看看它身子在哪块屏幕上（不看鼠标，不然鼠标一换屏它就跟着跳）。
    在屏幕边上的时候脚底可能正好在屏幕外面，所以看身子中间；哪块都不在就还算原来那块。"""
    global _screen
    body = local_to_world(pet, 0, -20)
    found = QGuiApplication.screenAt(QPoint(int(body.x()), int(body.y())))
    if found is not None:
        _screen = found


def pose_transform(pet):
    """当前的面对应的 (旋转角度, 要不要镜像)。原画是头朝左、肚子朝下。"""
    if pet.surface == "ceiling":
        return 180, pet.dir < 0
    if pet.surface == "wall":
        if pet.side == "L":
            return 90, pet.dir > 0
        return -90, pet.dir < 0
    return 0, pet.dir > 0


def local_to_world(pet, dx, dy):
    """把画面里相对脚底支点的偏移，换算成屏幕上的位置。"""
    deg, mirrored = pose_transform(pet)
    s = pet.scale()
    dx, dy = dx * s * (-1 if mirrored else 1), dy * s
    r = math.radians(deg)
    return QPointF(pet.ax + dx * math.cos(r) - dy * math.sin(r), pet.ay + dx * math.sin(r) + dy * math.cos(r))


# ---------------------------------------------------------------- 活动窗口

def check_window(pet):
    """看看活动窗口在哪；它脚下的窗口挪了就跟着挪，没了就吐丝下去。
    顺便量一下窗口挪得多快（pet.win_velocity，像素/秒）：被拖得飞快，它就死死抓住（behaviors/cling.py 的 hold_on）。"""
    hwnd, rect = pet.windows()
    pet.win_prev, pet.win = pet.win, rect
    pet.active_hwnd = hwnd
    now = time.time()
    dt, pet.win_seen_at = max(now - pet.win_seen_at, 0.03), now
    pet.win_velocity = (0.0, 0.0)
    if not pet.on_window or pet.state in ("lifted", "tug"):
        pet.win_hwnd = hwnd
        return
    if rect is None or hwnd != pet.win_hwnd:
        return emergency_silk(pet)
    old = pet.win_prev
    if old is not None and (old.left() != rect.left() or old.top() != rect.top()):
        dx, dy = rect.left() - old.left(), rect.top() - old.top()
        pet.ax += dx
        pet.ay += dy
        if old.size() == rect.size():                          # 整个窗口在挪（不是拖边改大小）
            pet.win_velocity = (dx / dt, dy / dt)
    if pet.win_edge == "top" and rect.width() < 3 * pet.sp.half * pet.scale():
        emergency_silk(pet)


def aim_for_window(pet):
    """在地上想去窗口：窗口底边贴着任务栏就朝它走，不然朝近的屏幕边走（爬上去再垂丝下来）。"""
    w, a = pet.win, area()
    if w is None:
        return
    if w.bottom() >= a.bottom() - 40:
        pet.dir = -1 if pet.ax > w.center().x() else 1
    else:
        pet.dir = -1 if pet.ax - a.left() < a.right() - pet.ax else 1


def want_window(pet):
    pet.goal_window = True
    pet.goal_until = time.time() + 60


# ---------------------------------------------------------------- 换面

def climb_onto(pet, surface, side, x, y, direction, win_edge):
    """爬到另一个面上，接着爬。"""
    pet.surface, pet.side, pet.dir = surface, side or pet.side, direction
    pet.on_window = win_edge is not None
    pet.win_edge = win_edge
    if pet.on_window:
        pet.win_hwnd, _ = pet.windows()
    if surface == "floor" and win_edge == "top":
        pet.goal_window = False
    pet.ax, pet.ay = x, y
    if surface == "wall" and direction < 0:
        pet.say("heave", 1.2)
    pet.start("crawl", random.uniform(4, 12))


def silk_from(pet, x, y):
    pet.start("hang", top=QPointF(x, y), fast=False)


def emergency_silk(pet):
    """脚下没东西了（窗口没了/被松手），马上吐丝，先快后慢。"""
    pet.start("hang", top=QPointF(pet.ax, pet.ay - 8 * pet.scale()), fast=True)


def landing_target(pet):
    """正下方先碰到谁：活动窗口的上沿，或者任务栏。返回 (y, 是不是窗口)。"""
    B = area().bottom() + 1
    w = pet.win
    half = pet.sp.half * pet.scale()
    if w is not None and w.left() + half * 0.6 < pet.ax < w.right() - half * 0.6 and w.top() > pet.ay:
        return w.top(), True
    return B, False


def land(pet, y, on_window, hard):
    pet.surface = "floor"
    pet.on_window = on_window
    pet.win_edge = "top" if on_window else None
    if on_window:
        pet.win_hwnd, _ = pet.windows()
        pet.goal_window = False
    pet.ay = y
    pet.dir = random.choice((-1, 1))
    if hard:
        pet.say("dots", 1.6)
    pet.start("idle", random.uniform(2, 5))


# ---------------------------------------------------------------- 爬一步

def wave_first(pet, edge):
    """到边上了：先抬起前半身晃一晃、探探路，晃完回来再真的决定怎么走。
    返回 True 表示这一拍先去探路了。edge 是 config.WAVE_CHANCE 里的哪种边。"""
    if pet.waved:                      # 刚探过路，这次照常决定
        pet.waved = False
        return False
    if random.random() < WAVE_CHANCE[edge]:
        pet.start("wave", edge=True)
        return True
    return False


def advance(pet):
    """沿着当前的面爬一拍；到头了决定转弯、爬到别的面，或者吐丝下去。"""
    s = pet.scale()
    half = pet.sp.half * s
    a = area()
    L, R, T, B = a.left(), a.right() + 1, a.top(), a.bottom() + 1
    w = pet.win
    speed = (CLIMB_SPEED if pet.surface == "wall" else CRAWL_SPEED) * s

    if pet.surface == "floor" and not pet.on_window:            # 任务栏
        front_before = pet.ax + pet.dir * half
        pet.ax += speed * pet.dir
        pet.ay = B
        front = pet.ax + pet.dir * half
        # 碰到贴着任务栏的活动窗口侧边：爬上去
        if w is not None and w.bottom() >= B - 40 and w.height() > 2 * half + 20:
            if pet.dir > 0 and front_before < w.left() <= front and pet.ax < w.left():
                if pet.goal_window or random.random() < 0.6:
                    return climb_onto(pet, "wall", "R", w.left(), min(w.bottom(), B) - half, -1, "left")
            if pet.dir < 0 and front_before > w.right() >= front and pet.ax > w.right():
                if pet.goal_window or random.random() < 0.6:
                    return climb_onto(pet, "wall", "L", w.right(), min(w.bottom(), B) - half, -1, "right")
        # 走到屏幕边：爬墙，或者掉头
        if pet.ax <= L + half or pet.ax >= R - half:
            pet.ax = min(max(pet.ax, L + half), R - half)
            if wave_first(pet, "screen_side"):
                return
            if pet.goal_window or random.random() < 0.45:
                if pet.ax <= L + half:
                    return climb_onto(pet, "wall", "L", L, B - half, -1, None)
                return climb_onto(pet, "wall", "R", R, B - half, -1, None)
            pet.dir = -pet.dir

    elif pet.surface == "floor":                                 # 活动窗口的上沿
        if w is None:
            return
        pet.ay = w.top()
        pet.ax += speed * pet.dir
        lo, hi = w.left() + half * 0.6, w.right() - half * 0.6
        if pet.ax <= lo or pet.ax >= hi:
            pet.ax = min(max(pet.ax, lo), hi)
            if wave_first(pet, "window_end"):
                return
            roll = random.random()
            at_left = pet.ax <= lo
            if roll < 0.35 and w.height() > 2 * half + 20:     # 翻过边角，顺着侧边往下爬
                if at_left:
                    return climb_onto(pet, "wall", "R", w.left(), w.top() + half, 1, "left")
                return climb_onto(pet, "wall", "L", w.right(), w.top() + half, 1, "right")
            if roll < 0.7:                                     # 从边角吐丝垂下去
                return silk_from(pet, w.left() - 14 * s if at_left else w.right() + 14 * s, w.top())
            pet.dir = -pet.dir

    elif pet.surface == "wall":
        pet.ay += speed * pet.dir
        if pet.on_window:
            if w is None:
                return
            pet.ax = w.left() if pet.win_edge == "left" else w.right()
            top, bottom = w.top() + half, min(w.bottom(), B) - half
        else:
            pet.ax = L if pet.side == "L" else R
            top, bottom = T + half, B - half
        if pet.ay <= top:                                      # 爬到顶了
            pet.ay = top
            if wave_first(pet, "wall_top"):
                return
            if pet.on_window:
                x = w.left() + half if pet.win_edge == "left" else w.right() - half
                return climb_onto(pet, "floor", None, x, w.top(), 1 if pet.win_edge == "left" else -1, "top")
            x = L + half if pet.side == "L" else R - half
            return climb_onto(pet, "ceiling", None, x, T, 1 if pet.side == "L" else -1, None)
        if pet.ay >= bottom:                                   # 爬到底了
            pet.ay = bottom
            if pet.on_window and w.bottom() < B - 40:          # 窗口底下悬空：吐丝下去
                if wave_first(pet, "window_hang"):
                    return
                return silk_from(pet, w.left() - 14 * s if pet.win_edge == "left" else w.right() + 14 * s, w.bottom())
            if pet.on_window:
                x = w.left() - half if pet.win_edge == "left" else w.right() + half
                return climb_onto(pet, "floor", None, x, B, -1 if pet.win_edge == "left" else 1, None)
            x = L + half if pet.side == "L" else R - half
            return climb_onto(pet, "floor", None, x, B, 1 if pet.side == "L" else -1, None)
        if not pet.goal_window and random.random() < 0.003:   # 偶尔改主意，掉头
            pet.dir = -pet.dir

    elif pet.surface == "ceiling":
        pet.ay = T
        pet.ax += speed * pet.dir
        # 正好在活动窗口上方：吐丝降到窗口上
        if w is not None and w.left() + half < pet.ax < w.right() - half:
            if random.random() < (0.08 if pet.goal_window else 0.02):
                return silk_from(pet, pet.ax, T)
        elif not pet.goal_window and random.random() < 0.004:  # 想去窗口的时候不乱跳
            return silk_from(pet, pet.ax, T)
        if pet.ax <= L + half or pet.ax >= R - half:          # 走到角上，顺着墙往下
            pet.ax = min(max(pet.ax, L + half), R - half)
            if wave_first(pet, "ceiling_end"):
                return
            if pet.ax <= L + half:
                return climb_onto(pet, "wall", "L", L, T + half, 1, None)
            return climb_onto(pet, "wall", "R", R, T + half, 1, None)
