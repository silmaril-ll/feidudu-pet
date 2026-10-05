"""
肥嘟嘟桌宠
==========
一只柑橘凤蝶的小绿虫，住在你的屏幕上。

它会自己爬、发呆、扭一扭，晚上爱睡觉。
它不只在任务栏上爬：会顺着屏幕边往上爬、倒挂着在屏幕顶上爬，
也会爬上「当前活动窗口」的侧边和上沿（最大化、全屏、最小化的窗口不爬）。
要下来的时候它会吐一根丝慢慢垂下来，不会摔着。窗口被拖走、关掉、切换了，它也会吐丝降落。

- 单击：戳它一下，多半扭扭～，有时冒出橙色小角（哼！）
- 双击：马上伪装成输入法（有人来了！）
- 按住往外拉：它会死死抓住（不放！），要用力拉住一会儿它才松手（哇啊～）
- 被拎起来：团成一个小 C 字，有点不高兴地扭；松手它吐丝降落
- 右键：喂叶子、扭一个、睡觉、大小、现在去窗口上、回到任务栏、退出

运行：双击本文件就行。第一次打开会先自己装一下 PyQt6（只装一次，要一两分钟）。
出了问题会弹个小框，详细的记在 feidudu_error.log 里。重复双击也只会有一只肥嘟嘟（会把它叫出来）。
画面都在 sprites 文件夹里（清单是 sprites/sprites.json），吃了几片叶子记在 feidudu_save.json 里。

程序在 feidudu_pet 文件夹里，一个动作一个文件（feidudu_pet/behaviors/），
加新动作的方法写在 feidudu_pet/behaviors/__init__.py 开头。
"""
import base64
import datetime
import importlib
import re
import subprocess
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOG = HERE / "feidudu_error.log"
CRASH_LOG = HERE / "feidudu_crash.log"
sys.path.insert(0, str(HERE))          # 从快捷方式、开机启动打开也找得到 feidudu_pet


def english():
    """my_config.py 里写了 LANGUAGE = "en"，弹出来的小框也说英文（这时候程序还没读进来，自己看一眼）。"""
    try:
        text = (HERE / "my_config.py").read_text(encoding="utf-8")
    except OSError:
        return False
    return re.search(r"""^\s*LANGUAGE\s*=\s*["']en["']""", text, re.M) is not None


EN = english()


def tr(zh, en):
    return en if EN else zh


def message(text):
    """双击 .pyw 没有黑窗口，有事就弹个小框说。"""
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, text, tr("肥嘟嘟", "FeiDuDu"), 0x40)
    elif sys.stderr:
        print(text, file=sys.stderr)


def log_error(kind, value, tb):
    """出错了：记到 feidudu_error.log。装了这个，程序里某一步出错也不会让肥嘟嘟整个消失。"""
    text = "".join(traceback.format_exception(kind, value, tb))
    try:
        if LOG.exists() and LOG.stat().st_size > 200_000:      # 太长了就从头记
            LOG.unlink()
        with LOG.open("a", encoding="utf-8") as f:
            f.write(f"\n==== {datetime.datetime.now():%Y-%m-%d %H:%M:%S}\n{text}")
    except OSError:
        pass
    if sys.stderr:
        print(text, file=sys.stderr)


def has_pyqt6():
    importlib.invalidate_caches()
    try:
        importlib.import_module("PyQt6.QtWidgets")
        return True
    except ImportError:
        return False


def ensure_pyqt6():
    """第一次打开：没有 PyQt6 就自己装一下。"""
    if has_pyqt6():
        return True
    message(tr("第一次打开，要先装一下 PyQt6（只用装一次）。\n点「确定」开始装，大概一两分钟，装好肥嘟嘟会自己出来。",
               "First time here: PyQt6 needs to be installed (only once).\nClick OK to start. It takes a minute or two, "
               "and FeiDuDu will come out by itself when it's done."))
    no_window = 0x08000000 if sys.platform == "win32" else 0     # 装的时候也不弹黑窗口
    result = subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "PyQt6"],
                            capture_output=True, text=True, creationflags=no_window)
    if has_pyqt6():
        return True
    log_error(RuntimeError, RuntimeError("PyQt6 没装上：\n" + result.stdout[-2000:] + result.stderr[-2000:]), None)
    message(tr("PyQt6 没装上 T_T\n可能是网络不通。详细的记在 feidudu_error.log 里。",
               "Couldn't install PyQt6 T_T\nMaybe there's no internet connection. Details are in feidudu_error.log."))
    return False


def make_shortcut():
    """在这个文件夹里放一个带肥嘟嘟图标（feidudu_icon.ico）的「肥嘟嘟」快捷方式：
    .pyw 文件自己换不了图标（Windows 按文件类型给图标），快捷方式可以。以后点它、或者把它拖到桌面、开机启动文件夹都行。
    每次打开都在后台悄悄更新一遍，整个文件夹挪了地方也还对。只在 Windows 上做，做不成也不要紧。"""
    if sys.platform != "win32":
        return
    exe = Path(sys.executable)
    pythonw = exe.with_name("pythonw.exe") if exe.with_name("pythonw.exe").exists() else exe

    def q(path):
        return str(path).replace("'", "''")             # PowerShell 单引号字符串里的单引号要写两遍
    script = (f"$s = (New-Object -ComObject WScript.Shell).CreateShortcut('{q(HERE / '肥嘟嘟.lnk')}'); "
              f"$s.TargetPath = '{q(pythonw)}'; $s.Arguments = '\"{q(HERE / 'feidudu.pyw')}\"'; "
              f"$s.WorkingDirectory = '{q(HERE)}'; $s.IconLocation = '{q(HERE / 'feidudu_icon.ico')},0'; "
              "$s.Description = '肥嘟嘟桌宠'; $s.Save()")
    encoded = base64.b64encode(script.encode("utf-16-le")).decode()   # 这样中文路径也不会乱码
    try:
        subprocess.Popen(["powershell", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
                         creationflags=0x08000000)       # 不弹黑窗口，也不等它
    except OSError:
        pass


# 少了这些，肥嘟嘟就出不来（比如只下载了一部分、解压的时候漏了、同步盘还没同步完）
NEEDED = ("feidudu_pet/__init__.py", "feidudu_pet/app.py", "feidudu_pet/pet.py", "feidudu_pet/behaviors/__init__.py",
          "sprites/sprites.json")


def files_ok():
    """看看文件齐不齐：缺了就直接说缺哪几个，比 Python 那句看不懂的报错好。"""
    missing = [name for name in NEEDED if not (HERE / name).exists()]
    if not missing:
        return True
    log_error(FileNotFoundError, FileNotFoundError(f"在 {HERE} 里找不到：{', '.join(missing)}"), None)
    message(tr("肥嘟嘟的文件好像不全，缺了：\n", "Some of FeiDuDu's files are missing:\n") + "\n".join(missing)
            + tr("\n\n请重新下载完整的项目（GitHub 上 Code → Download ZIP，整个解压），"
                 "把 feidudu_save.json 复制过去就能接着玩。",
                 "\n\nPlease download the whole project again (on GitHub: Code → Download ZIP, unzip all of it), "
                 "then copy feidudu_save.json over to keep your progress."))
    return False


def where_it_looked():
    """出错的时候顺便记下：Python 到底用的是哪个 feidudu_pet 文件夹、它在哪些地方找（方便查问题）。"""
    found = sys.modules.get("feidudu_pet")
    return (f"本文件夹：{HERE}\n用到的 feidudu_pet：{list(getattr(found, '__path__', [])) if found else '没有'}\n"
            f"找模块的地方：{sys.path[:4]}")


def black_box():
    """闪退（Python 接不住的那种）的时候，把当时在跑哪几行记到 feidudu_crash.log，方便查。"""
    import faulthandler
    try:
        if CRASH_LOG.exists() and CRASH_LOG.stat().st_size > 200_000:
            CRASH_LOG.unlink()
        crash_file = CRASH_LOG.open("a", encoding="utf-8")
        crash_file.write(f"\n==== 启动 {datetime.datetime.now():%Y-%m-%d %H:%M:%S}\n")
        crash_file.flush()
        faulthandler.enable(file=crash_file, all_threads=True)
        return crash_file                                   # 留着，不然文件被关掉就记不了了
    except OSError:
        return None


if __name__ == "__main__":
    sys.excepthook = log_error
    _crash_file = black_box()
    if files_ok() and ensure_pyqt6():
        make_shortcut()
        try:
            from feidudu_pet.app import main
            main()
        except SystemExit:
            raise
        except Exception:
            kind, value, tb = sys.exc_info()
            log_error(kind, value, tb)
            log_error(RuntimeError, RuntimeError(where_it_looked()), None)
            message(tr("肥嘟嘟没能出来，出错的详细记在 feidudu_error.log 里。",
                       "FeiDuDu couldn't start. Details are in feidudu_error.log."))
