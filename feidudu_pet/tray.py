"""右下角托盘里的小图标：一只正面的蝴蝶剪影（柑橘凤蝶的样子：上翅大、下翅带小尾巴）。
托盘里只有 16–32 像素，所以不用蜡笔画，直接用线条画成剪影，每个尺寸都清楚。
颜色跟着系统：深色任务栏用奶白色，浅色任务栏用炭灰色；系统换主题时跟着换。"""
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QGuiApplication, QIcon, QPainter, QPainterPath, QPixmap
from PyQt6.QtWidgets import QSystemTrayIcon

from .menu import crayon_menu
from .toys import put_away
from .lang import tr

LIGHT_INK = QColor("#f6efe0")      # 深色任务栏上
DARK_INK = QColor("#3a3330")       # 浅色任务栏上


def butterfly_path():
    """左半边的两片翅膀（100×100 的格子里）；右半边画的时候照镜子。"""
    half = QPainterPath()
    half.moveTo(48, 44)                                   # 上翅：大，往左上张开
    half.cubicTo(38, 30, 22, 14, 10, 16)
    half.cubicTo(2, 18, 4, 34, 12, 44)
    half.cubicTo(20, 52, 36, 54, 48, 52)
    half.closeSubpath()
    half.moveTo(48, 55)                                   # 下翅：小一点，带一条小尾巴（凤蝶的尾突）
    half.cubicTo(34, 56, 18, 62, 20, 72)
    half.cubicTo(22, 80, 30, 80, 34, 76)
    half.lineTo(31, 92)
    half.lineTo(39, 76)
    half.cubicTo(44, 70, 48, 64, 48, 55)
    half.closeSubpath()
    return half


def draw_butterfly(size, ink):
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.scale(size / 100, size / 100)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(ink)
    half = butterfly_path()
    p.drawPath(half)
    p.save()
    p.translate(100, 0)
    p.scale(-1, 1)                                        # 右半边 = 左半边照镜子
    p.drawPath(half)
    p.restore()
    p.drawRoundedRect(QRectF(46.5, 36, 7, 42), 3.5, 3.5)  # 身子
    pen = p.pen()
    pen.setColor(ink)
    pen.setStyle(Qt.PenStyle.SolidLine)
    pen.setWidthF(3.2)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    antenna = QPainterPath(QPointF(48.5, 38))             # 触角，末端一个小圆头
    antenna.cubicTo(46, 28, 42, 20, 37, 14)
    p.drawPath(antenna)
    p.save()
    p.translate(100, 0)
    p.scale(-1, 1)
    p.drawPath(antenna)
    p.restore()
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(ink)
    p.drawEllipse(QPointF(37, 14), 3.6, 3.6)
    p.drawEllipse(QPointF(63, 14), 3.6, 3.6)
    p.end()
    return pix


def butterfly_icon():
    """按现在是深色还是浅色主题，挑颜色，画好各种尺寸。"""
    dark = True
    hints = QGuiApplication.styleHints()
    if hasattr(hints, "colorScheme"):                     # Qt 6.5 以后才有
        dark = hints.colorScheme() != Qt.ColorScheme.Light
    ink = LIGHT_INK if dark else DARK_INK
    icon = QIcon()
    for size in (16, 20, 24, 32, 40, 48, 64):
        icon.addPixmap(draw_butterfly(size, ink))
    return icon


def make_tray(app, pet, sprites):
    if not QSystemTrayIcon.isSystemTrayAvailable():
        return None
    tray = QSystemTrayIcon(butterfly_icon(), app)
    hints = QGuiApplication.styleHints()
    if hasattr(hints, "colorSchemeChanged"):               # 系统换了深色/浅色主题，图标跟着换
        hints.colorSchemeChanged.connect(lambda *_: tray.setIcon(butterfly_icon()))
    tray.setToolTip(tr("肥嘟嘟", "FeiDuDu"))
    menu = crayon_menu()
    toy = menu.addAction(tr("收起玩具", "Put the toy away"), lambda *_: put_away(pet))      # 拿着玩具的时候才有这一项
    pause = menu.addAction(tr("安静一会儿", "Quiet time"), pet.toggle_pause)                 # 打游戏的时候：暂停、藏起来
    pause.setCheckable(True)
    menu.aboutToShow.connect(lambda: (pause.setChecked(bool(pet.paused)), toy.setVisible(pet.toy is not None)))
    menu.addAction(tr("回到任务栏上", "Back to the taskbar"), lambda *_: (pet.unpause(), pet.undisguise(), pet.show(), pet.back_to_floor()))   # 万一卡在奇怪的地方
    menu.addSeparator()
    menu.addAction(tr("让它去睡（退出）", "Put it to bed (quit)"), app.quit)
    tray.setContextMenu(menu)

    def clicked(reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:      # 单击：睡着就叫它出来，醒着就扭一扭
            pet.unpause() if pet.paused else pet.wiggle()
    tray.activated.connect(clicked)
    tray.show()
    tray.menu = menu          # 留个引用，不然菜单会被回收
    return tray
