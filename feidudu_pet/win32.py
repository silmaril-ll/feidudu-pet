"""只有这个文件会碰 Windows 的 API：找活动窗口、让肥嘟嘟不抢焦点、伪装的快捷键。别的系统上什么都不做。"""
import os
import sys

from PyQt6.QtCore import QRect, Qt, QTimer
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import QWidget

IS_WINDOWS = sys.platform == "win32"


class ActiveWindow:
    """找到当前活动窗口，返回它在屏幕上的矩形（Qt 的逻辑像素）。

    和 Shimeji 一样只认活动窗口。跳过：肥嘟嘟自己、桌面、任务栏、最小化、最大化、全屏、太小的窗口。
    点肥嘟嘟、开它的右键菜单时，活动窗口会暂时变成它自己，这时继续用上一个窗口。
    """

    SKIP_CLASSES = {"Progman", "WorkerW", "Shell_TrayWnd", "Shell_SecondaryTrayWnd", "NotifyIconOverflowWindow"}

    def __init__(self):
        self.last_hwnd = None
        if not IS_WINDOWS:
            return
        import ctypes
        from ctypes import wintypes
        self.ct, self.wt = ctypes, wintypes
        self.user32 = ctypes.windll.user32
        self.dwm = ctypes.windll.dwmapi
        self.user32.GetForegroundWindow.restype = wintypes.HWND
        for fn in ("IsWindowVisible", "IsIconic", "IsZoomed", "IsWindow"):
            getattr(self.user32, fn).argtypes = [wintypes.HWND]
        self.user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        self.user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        self.dwm.DwmGetWindowAttribute.argtypes = [wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]
        self.own_pid = os.getpid()

    def _pid(self, hwnd):
        pid = self.wt.DWORD()
        self.user32.GetWindowThreadProcessId(hwnd, self.ct.byref(pid))
        return pid.value

    def _rect(self, hwnd):
        """窗口看得见的边框（物理像素）。GetWindowRect 在 Win10/11 上会多算一圈隐形边框。"""
        rect = self.wt.RECT()
        ok = self.dwm.DwmGetWindowAttribute(hwnd, 9, self.ct.byref(rect), self.ct.sizeof(rect)) == 0   # 9 = 真实可见边框
        if not ok:
            self.user32.GetWindowRect(hwnd, self.ct.byref(rect))
        cloaked = self.ct.c_int(0)
        self.dwm.DwmGetWindowAttribute(hwnd, 14, self.ct.byref(cloaked), self.ct.sizeof(cloaked))    # 14 = 被系统藏起来的窗口
        return rect, cloaked.value != 0

    def _usable(self, hwnd):
        if not hwnd or not self.user32.IsWindow(hwnd) or not self.user32.IsWindowVisible(hwnd):
            return None
        if self.user32.IsIconic(hwnd) or self.user32.IsZoomed(hwnd):
            return None
        name = self.ct.create_unicode_buffer(256)
        self.user32.GetClassNameW(hwnd, name, 256)
        if name.value in self.SKIP_CLASSES:
            return None
        rect, cloaked = self._rect(hwnd)
        if cloaked:
            return None
        screen = QGuiApplication.primaryScreen()
        dpr = screen.devicePixelRatio()                  # Windows 的缩放比例，125% 就是 1.25
        logical = QRect(round(rect.left / dpr), round(rect.top / dpr),
                        round((rect.right - rect.left) / dpr), round((rect.bottom - rect.top) / dpr))
        full = screen.geometry()
        if logical.width() >= full.width() - 2 and logical.height() >= full.height() - 2:
            return None                                  # 全屏
        if logical.width() < 240 or logical.height() < 160:
            return None                                  # 太小，爬不上去
        return logical

    def rect(self):
        """返回 (窗口编号, 矩形)，没有可爬的窗口就返回 (None, None)。"""
        if not IS_WINDOWS:
            return None, None
        hwnd = self.user32.GetForegroundWindow()
        if hwnd and self._pid(hwnd) == self.own_pid:
            hwnd = self.last_hwnd                        # 刚点了肥嘟嘟自己，窗口还算上一个
        r = self._usable(hwnd)
        self.last_hwnd = hwnd if r is not None else None
        return (hwnd, r) if r is not None else (None, None)


def no_activate(widget):
    """让窗口被点的时候不抢焦点，不然一点它，活动窗口就变成它自己了。"""
    if not IS_WINDOWS:
        return
    import ctypes
    hwnd = int(widget.winId())
    GWL_EXSTYLE, WS_EX_NOACTIVATE = -20, 0x08000000
    style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_NOACTIVATE)


def idle_seconds():
    """人多久没碰键盘鼠标了（秒）：GetLastInputInfo。别的系统上返回 None（senses.py 就改看鼠标有没有动）。
    滚轮、按键、挪鼠标都算“碰了”。"""
    if not IS_WINDOWS:
        return None
    import ctypes
    from ctypes import wintypes

    class LASTINPUTINFO(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]
    info = LASTINPUTINFO(ctypes.sizeof(LASTINPUTINFO), 0)
    if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info)):
        return None
    now = ctypes.windll.kernel32.GetTickCount() & 0xFFFFFFFF
    return ((now - info.dwTime) & 0xFFFFFFFF) / 1000         # 两个都是毫秒计数，49 天会绕回来一次


def buttons_down():
    """鼠标键现在是不是按着（在别的程序里按也算）。别的系统上只知道在肥嘟嘟自己窗口里按的。"""
    if not IS_WINDOWS:
        return QGuiApplication.mouseButtons() != Qt.MouseButton.NoButton
    import ctypes
    state = ctypes.windll.user32.GetAsyncKeyState
    state.restype = ctypes.c_short
    return any(state(vk) & 0x8000 for vk in (0x01, 0x02, 0x04))     # 左键、右键、中键


def foreground_app():
    """最前面那个窗口是哪个程序：(程序名, 窗口标题)，比如 ("GenshinImpact.exe", "原神")。
    读不到的就是空字符串（有的游戏带反作弊，不让读程序名，标题一般还是读得到）。别的系统上返回 None。"""
    if not IS_WINDOWS:
        return None
    import ctypes
    from ctypes import wintypes
    user32, kernel32 = ctypes.windll.user32, ctypes.windll.kernel32
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
                                                    ctypes.POINTER(wintypes.DWORD)]
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return "", ""
    title = ctypes.create_unicode_buffer(512)
    user32.GetWindowTextW(hwnd, title, 512)
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    exe = ""
    handle = kernel32.OpenProcess(0x1000, False, pid.value)      # 0x1000 = 只查名字，权限最小
    if handle:
        try:
            buf, size = ctypes.create_unicode_buffer(1024), wintypes.DWORD(1024)
            if kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
                exe = buf.value.rsplit("\\", 1)[-1]
        finally:
            kernel32.CloseHandle(handle)
    return exe, title.value


# ---------------------------------------------------------------- 全局快捷键

MODIFIERS = {"ctrl": 0x2, "control": 0x2, "alt": 0x1, "shift": 0x4, "win": 0x8}
MOD_NOREPEAT = 0x4000       # 按住不放不会一直触发
WM_HOTKEY = 0x0312


def parse_hotkey(text):
    """"Ctrl+Alt+Z" → (修饰键, 按键码)。要至少一个修饰键加一个字母/数字/F1–F24；认不出来返回 None。"""
    mods, key = 0, None
    for part in text.replace(" ", "").split("+"):
        low = part.lower()
        if low in MODIFIERS:
            mods |= MODIFIERS[low]
        elif len(part) == 1 and part.isascii() and part.isalnum():
            key = ord(part.upper())
        elif low[:1] == "f" and low[1:].isdigit() and 1 <= int(low[1:]) <= 24:
            key = 0x70 + int(low[1:]) - 1
        else:
            return None
    return (mods, key) if mods and key else None


class GlobalHotkey(QWidget):
    """在哪个程序里按都有用的快捷键（RegisterHotKey）。
    注册在一个不显示的小窗口上：Windows 只把 WM_HOTKEY 发给这个小窗口，程序别的消息都不经过这里
    （以前用全局的 nativeEventFilter，所有消息都要过一遍 Python，开菜单时消息一多，有闪退的嫌疑）。
    按到了也不在消息里直接做事，而是排到下一轮再做（QTimer.singleShot）。
    别的系统上、组合键认不出来、或者被别的程序占了：ok 是 False。"""

    ID = 0xF1D0

    def __init__(self, text, callback):
        super().__init__(None, Qt.WindowType.Tool)
        self.callback = callback
        self.ok = False
        parsed = parse_hotkey(text)
        if not IS_WINDOWS or parsed is None:
            return
        import ctypes
        from ctypes import wintypes
        self.msg_type = wintypes.MSG
        self.user32 = ctypes.windll.user32
        self.user32.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT]
        self.user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
        self.hwnd = int(self.winId())                     # 不 show，只要它有个窗口句柄
        self.ok = bool(self.user32.RegisterHotKey(self.hwnd, self.ID, parsed[0] | MOD_NOREPEAT, parsed[1]))

    def nativeEvent(self, event_type, message):
        if self.ok:
            msg = self.msg_type.from_address(int(message))
            if msg.message == WM_HOTKEY and msg.wParam == self.ID:
                QTimer.singleShot(0, self.callback)
                return True, 0
        return False, 0

    def release(self):
        if self.ok:
            self.user32.UnregisterHotKey(self.hwnd, self.ID)
            self.ok = False
