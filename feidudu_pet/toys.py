"""玩具：小卖部里买一次就永久拥有（存档 save["toys"]），右键「玩具箱」拿出来玩。货架和样子在 art-source/items.js 的 TOYS。

现在只有一样：
  拿在手上的逗虫棒：一个透明、点不到的小窗口跟着鼠标走（HandToy），pet.toy 是正拿着的那样。
    树枝头垂着一根软线（Line：能甩、能被坠长一点再弹回来），线头拴着叶子，叶子顺着线转。
    逗虫棒 → 它追着叶子跑、抬头够（behaviors/chase.py）；叶子在嘴边停一会儿它就咬住，和你拔河（behaviors/tussle.py）：
    这时叶柄咬在它嘴里（HandToy.mouth），线两头都拴住，离得近就垂下来，拉远了就绷直。
玩累了：拿着玩具、它真的在玩的时间攒够 TOY_PLAY 秒，就“玩累了…”，收起来，TOY_REST 分钟里不肯再玩。
下架了的玩具（存档里有、货架上没有）就当没有。"""
import math
import random
import time

from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer
from PyQt6.QtGui import QColor, QCursor, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QWidget

from .config import TOY_PLAY, TOY_REST, WAND_DAMP, WAND_GRAVITY, WAND_LINE, WAND_STRETCH
from .lang import tr
from .menu import add_submenu
from .win32 import no_activate

FRAME_MS = 33                 # 跟着鼠标、算线怎么晃：一秒 30 帧
HAND = ("wand",)
PLAYING = ("chase", "tussle")              # 这些时候算“在玩”，攒玩累的时间


def click_through(widget):
    """透明、点不到、不抢焦点的小窗口（和丝、礼花一样）。"""
    widget.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
                          | Qt.WindowType.Tool | Qt.WindowType.WindowTransparentForInput
                          | Qt.WindowType.WindowDoesNotAcceptFocus)
    widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
    widget.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)


def size_of(pix):
    return pix.width() / pix.devicePixelRatio(), pix.height() / pix.devicePixelRatio()


# ---------------------------------------------------------------- 逗虫棒的软线

NODES = 8                     # 线分成几小节（一串小珠子）
SUBSTEPS = 8                  # 每帧分几小步算（越多越稳，不会抖）
LEAF_MASS, BEAD = 1.0, 0.06   # 叶子多重、线上每颗小珠子多重（叶子重，线就被它坠着、甩着）
LEAF_HANG = 100               # 画里叶子朝哪个方向垂着（度，items.js 里 place 的 1.75 弧度）
LONGEST = 1.4                 # 线最多被拉到原来的几倍长，再长就绷紧了
AIR = 0.006                   # 叶子的空气阻力：越快挡得越狠（不然一甩就绕着树枝转圈）
SPRING_DAMP = 0.2             # 线被拉长又弹回来的那一下，每小步消掉这么多（不然像弹簧一样一直上下蹦）


class Line:
    """软线：一串小珠子，相邻两颗之间是能拉长一点的小皮筋。
    第一颗拴在树枝头；最后一颗是叶柄，平时自由地坠着、甩着，拔河的时候被它咬着、也拴死。
    算法是 XPBD（小步数的位置约束）：每小步先按惯性和重力走，再把每一节拉回原来的长度，
    拉回去时留一点“软”（compliance），线就能被坠长、被甩长，再弹回来。"""

    def __init__(self):
        self.pos, self.old = [], []
        self.top = self.bottom = None      # 上一帧两头拴在哪（bottom = None：叶子自由）
        self.still = 0                     # 连着几帧几乎没动（够多了就不算、不重画）

    def reset(self, top, length):
        """直直地垂在树枝头下面。"""
        self.pos = [[top.x(), top.y() + length * i / (NODES - 1)] for i in range(NODES)]
        self.old = [q[:] for q in self.pos]
        self.top, self.bottom, self.still = (top.x(), top.y()), None, 0

    def resting(self, top, bottom):
        return self.still > 10 and (top.x(), top.y()) == self.top and bottom == self.bottom

    def step(self, top, bottom, length, heavy, k):
        """往前算一帧。top：树枝头；bottom：叶柄被咬在哪（None = 自由）；heavy：线头挂没挂着叶子。"""
        top = (top.x(), top.y())
        bottom = (bottom.x(), bottom.y()) if bottom is not None else None
        t0 = self.top or top
        b0 = self.bottom or bottom
        h = FRAME_MS / 1000 / SUBSTEPS
        seg = length / (NODES - 1)
        # 叶子静静挂着时线被坠长 WAND_STRETCH：每一节都分一点
        soft = WAND_STRETCH * k / (LEAF_MASS * WAND_GRAVITY * (NODES - 1)) / (h * h)
        keep = math.exp(-WAND_DAMP * h)
        w = [0.0] + [1 / BEAD] * (NODES - 2) + [(1 / LEAF_MASS if heavy else 1 / BEAD) if bottom is None else 0.0]
        fall = WAND_GRAVITY * h * h
        cap = 4000 * h                     # 一小步最多走这么远（鼠标瞬移的时候别甩飞）
        moved = 0.0
        for n in range(1, SUBSTEPS + 1):
            f = n / SUBSTEPS                # 两头在这一帧里是慢慢挪过去的
            self.pos[0] = [t0[0] + (top[0] - t0[0]) * f, t0[1] + (top[1] - t0[1]) * f]
            if bottom is not None:
                b = b0 or bottom
                self.pos[-1] = [b[0] + (bottom[0] - b[0]) * f, b[1] + (bottom[1] - b[1]) * f]
            for i in range(1, NODES):
                if w[i] == 0:
                    continue
                q, o = self.pos[i], self.old[i]
                vx, vy = (q[0] - o[0]) * keep, (q[1] - o[1]) * keep
                v = math.hypot(vx, vy)
                if i == NODES - 1 and heavy:    # 叶子兜着风
                    slow = 1 / (1 + AIR * v)       # 每小步：速度（像素/秒）× 时间 = v
                    vx, vy, v = vx * slow, vy * slow, v * slow
                if v > cap:
                    vx, vy = vx * cap / v, vy * cap / v
                moved = max(moved, v)
                self.old[i] = q[:]
                self.pos[i] = [q[0] + vx, q[1] + vy + fall]
            for i in range(NODES - 1):      # 每一节拉回原来的长度（留一点软）
                a, b = self.pos[i], self.pos[i + 1]
                wa, wb = w[i], w[i + 1]
                if wa + wb == 0:
                    continue
                dx, dy = b[0] - a[0], b[1] - a[1]
                d = math.hypot(dx, dy) or 1e-6
                lam = -(d - seg) / (wa + wb + soft)
                nx, ny = dx / d, dy / d
                a[0] -= wa * lam * nx
                a[1] -= wa * lam * ny
                b[0] += wb * lam * nx
                b[1] += wb * lam * ny
                # 沿着线方向的来回弹，消掉一点
                oa, ob = self.old[i], self.old[i + 1]
                rel = ((b[0] - ob[0]) - (a[0] - oa[0])) * nx + ((b[1] - ob[1]) - (a[1] - oa[1])) * ny
                c = rel * SPRING_DAMP / (wa + wb)
                a[0] += wa * c * nx
                a[1] += wa * c * ny
                b[0] -= wb * c * nx
                b[1] -= wb * c * ny
            for i in range(1, NODES):           # 拉到头了就绷紧：每颗珠子离树枝头不能超过它那一截线的 LONGEST 倍
                q = self.pos[i]
                if w[i] == 0:
                    continue
                dx, dy = q[0] - self.pos[0][0], q[1] - self.pos[0][1]
                d, most = math.hypot(dx, dy), seg * i * LONGEST
                if d > most:
                    q[0] -= dx * (1 - most / d)
                    q[1] -= dy * (1 - most / d)
            self.old[0] = self.pos[0][:]
            if bottom is not None:
                self.old[-1] = self.pos[-1][:]
        self.top, self.bottom = top, bottom
        self.still = self.still + 1 if moved < 0.02 else 0

    def angle(self):
        """最后一节（拴着叶子那一节）朝哪（度）。"""
        a, b = self.pos[-2], self.pos[-1]
        return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))

    def path(self, origin):
        """画线用：顺着珠子画一条圆滑的曲线。"""
        pts = [QPointF(x, y) - origin for x, y in self.pos]
        path = QPainterPath(pts[0])
        for a, b in zip(pts[1:-1], pts[2:]):
            path.quadTo(a, (a + b) / 2)
        path.lineTo(pts[-1])
        return path


# ---------------------------------------------------------------- 拿在鼠标上的玩具

class HandToy(QWidget):
    """跟着鼠标走的逗虫棒：树枝画面里的 grip 点对着鼠标箭头尖，树枝头上垂着一根软线（Line），线头拴着叶子。"""

    def __init__(self):
        super().__init__(None)
        click_through(self)
        self.toy = None
        self.k = 1.0
        self.bare_until = 0.0              # 逗虫棒的叶子被咬走了，到这个时候才长回来
        self.mouth = None                  # 拔河的时候：叶子咬在它嘴里，嘴在屏幕上的哪（None = 叶子挂在线上）
        self.line = Line()
        self.turn = 0.0                    # 叶子跟着线转了多少度（0 = 和画里一样）
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.follow)

    def hold(self, toy, scale):
        self.toy, self.k = toy, max(scale, 0.6) * 1.1
        self.mouth = None
        self.line.reset(self.end(), self.line_length() + WAND_STRETCH * self.k)
        self.turn = 90 - LEAF_HANG                # 直直垂着：叶子顺着线往下
        self.follow()
        self.show()
        no_activate(self)
        self.timer.start(FRAME_MS)

    def drop(self):
        self.timer.stop()
        self.toy = None
        self.hide()

    def offset(self, name):
        """树枝画面上某个点离鼠标箭头尖多远。"""
        pts = self.toy["points"]
        return (pts[name] - pts["grip"]) * self.k

    def leaf_point(self, name):
        """叶子上某个点（tip 之类）离叶柄多远：叶子跟着线转。"""
        pts = self.toy["points"]
        d = (pts[name] - pts["stem"]) * self.k
        a = math.radians(self.turn)
        return QPointF(d.x() * math.cos(a) - d.y() * math.sin(a), d.x() * math.sin(a) + d.y() * math.cos(a))

    def stem(self):
        return QPointF(*self.line.pos[-1])

    def tip(self):
        """它追、它咬的那个地方（叶子靠叶柄的一头）。"""
        return self.stem() + self.leaf_point("tip")

    def bare(self):
        return time.time() < self.bare_until

    def line_length(self):
        return WAND_LINE * self.k

    def end(self):
        """树枝头（线从这儿垂下去）在屏幕上的位置。"""
        return QPointF(QCursor.pos()) + self.offset("end")

    def follow(self):
        """每帧：算线怎么晃，窗口罩住树枝、线和叶子。鼠标、嘴都没动，线也晃停了，就不用算、不用重画。"""
        if self.toy is None:
            return
        end = self.end()
        if self.mouth is not None:                  # 拔河：叶柄拴在它嘴边，叶子慢慢转回画里的样子
            self.turn += -self.turn * 0.3
            bottom = self.mouth - self.leaf_point("tip")
        else:
            bottom = None
        if self.line.resting(end, (bottom.x(), bottom.y()) if bottom is not None else None):
            return
        self.line.step(end, bottom, self.line_length(), not self.bare(), self.k)
        if self.mouth is None:                      # 叶子顺着最后一节线（慢半拍，像被甩着）
            want = self.line.angle() - LEAF_HANG
            self.turn += ((want - self.turn + 180) % 360 - 180) * 0.35
            self.turn = (self.turn + 180) % 360 - 180
        pos = QCursor.pos()
        grip = self.toy["points"]["grip"] * self.k
        w, h = size_of(self.toy["pix"])
        box = QRectF(pos.x() - grip.x(), pos.y() - grip.y(), w * self.k, h * self.k)
        xs, ys = [q[0] for q in self.line.pos], [q[1] for q in self.line.pos]
        pad = 40 * self.k                            # 叶子转起来能伸出去这么远
        box = box.united(QRectF(min(xs) - pad, min(ys) - pad, max(xs) - min(xs) + 2 * pad, max(ys) - min(ys) + 2 * pad))
        self.setGeometry(box.toAlignedRect())
        self.update()

    def paintEvent(self, event):
        if self.toy is None:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        origin = QPointF(self.x(), self.y())
        pts = self.toy["points"]
        stick = QPointF(QCursor.pos()) - pts["grip"] * self.k - origin      # 树枝画面左上角在窗口里的位置
        p.setPen(QPen(QColor(160, 138, 106), 1.6 * self.k))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(self.line.path(origin))
        p.save()
        p.translate(stick)
        p.scale(self.k, self.k)
        p.drawPixmap(QPointF(0, 0), self.toy["bare"])
        p.restore()
        if self.mouth is not None or not self.bare():   # 叶子：叶柄对着线头，跟着线转
            p.translate(self.stem() - origin)
            p.rotate(self.turn)
            p.scale(self.k, self.k)
            p.drawPixmap(-pts["stem"], self.toy["leaf"])
        p.end()


# ---------------------------------------------------------------- 拿出来、收起来、玩累了

def owned(pet):
    return [n for n in pet.save.get("toys", []) if n in pet.sp.toys]


def tired_minutes(pet):
    """还要歇几分钟（不累就是 0）。"""
    left = pet.toy_rest_until - time.time()
    return max(1, math.ceil(left / 60)) if left > 0 else 0


def use(pet, name):
    """拿出一样玩具（手上的那种）。已经拿着别的就先换下来。"""
    if tired_minutes(pet):
        return pet.say("tired", 1.8)
    put_away(pet, quiet=True)
    pet.toy = name
    pet.hand.hold(pet.sp.toys[name], pet.scale())
    pet.say("play", 1.6)


def put_away(pet, quiet=False):
    if pet.toy is None:
        return
    pet.toy = None
    pet.hand.drop()
    if pet.state in ("chase", "tussle"):
        pet.start("idle", random.uniform(2, 4))


def get_tired(pet):
    pet.toy_rest_until = time.time() + TOY_REST * 60
    pet.toy_played = 0.0
    put_away(pet)
    pet.say("tired", 2.2)


def tick(pet):
    """每拍在 pet.step 里调：攒玩的时间、逗虫棒拿着的时候让它去追。"""
    if pet.toy is None:
        return
    if pet.senses.away:                                 # 人都走开了，玩具收起来
        return put_away(pet, quiet=True)
    if pet.state in PLAYING:
        pet.toy_played += 0.09
        if pet.toy_played >= TOY_PLAY:
            return get_tired(pet)
    if pet.toy == "wand" and pet.state in ("idle", "crawl", "look", "approach") and pet.surface == "floor":
        pet.start("chase")


# ---------------------------------------------------------------- 右键菜单

def add_to_menu(menu, pet):
    """右键「玩具箱」：拿出来 / 收起来；拿着玩具的时候，右键菜单最上面还有一项「收起xx」。"""
    mine = owned(pet)
    if not mine:
        return
    box = add_submenu(menu, tr("玩具箱", "Toy box"))
    rest = tired_minutes(pet)
    for name in mine:
        toy = pet.sp.toys[name]
        label = toy["label"]
        if name in HAND:
            holding = pet.toy == name
            if rest and not holding:
                label += tr(f"（玩累了，还要 {rest} 分钟）", f" (tired, {rest} more min)")
            action = box.addAction(label, lambda *_, n=name: put_away(pet) if pet.toy == n else use(pet, n))
            action.setCheckable(True)
            action.setChecked(holding)
            action.setEnabled(holding or not rest)


def put_away_label(pet):
    """拿着玩具时右键菜单最上面那一项的字。"""
    return tr(f"收起{pet.sp.toys[pet.toy]['label']}", f"Put away the {pet.sp.toys[pet.toy]['label'].lower()}")

