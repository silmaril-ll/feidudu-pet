"""把所有东西拼起来，启动。"""
import getpass
import sys

from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from PyQt6.QtWidgets import QApplication

from .pet import FeiDuDu
from .sprites import Sprites
from .config import HOTKEY
from .tray import make_tray
from .win32 import GlobalHotkey


INSTANCE = "feidudu-desktop-pet-" + getpass.getuser()     # 同一个人只开一只


def already_running():
    """已经有一只在了：叫它出来，这边就不再开第二只。"""
    sock = QLocalSocket()
    sock.connectToServer(INSTANCE)
    if not sock.waitForConnected(300):
        return False
    sock.write(b"show")
    sock.waitForBytesWritten(300)
    sock.disconnectFromServer()
    return True


def listen_for_second_launch(app, pet):
    """再双击一次 feidudu.pyw 时：藏着的话就出来，打个招呼。"""
    QLocalServer.removeServer(INSTANCE)                 # 上次没关干净留下的
    server = QLocalServer(app)
    server.listen(INSTANCE)

    def come_out():
        server.nextPendingConnection()
        pet.unpause()
        pet.undisguise()
        pet.show()
        pet.greet()
    server.newConnection.connect(come_out)
    return server


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    if already_running():
        return
    sprites = Sprites()
    app.setWindowIcon(sprites.icon)
    pet = FeiDuDu(sprites)
    pet.show()
    app.tray = make_tray(app, pet, sprites)   # 留个引用，不然托盘图标会被回收
    pet.tray = app.tray                       # 伪装的时候要把托盘图标也藏起来
    app.server = listen_for_second_launch(app, pet)
    # 快捷键：藏着就出来，没藏就藏起来
    app.hotkey = GlobalHotkey(HOTKEY, lambda: pet.unpause() if pet.paused else pet.undisguise() if pet.ime.isVisible() else pet.disguise())
    app.aboutToQuit.connect(app.hotkey.release)
    sys.exit(app.exec())
