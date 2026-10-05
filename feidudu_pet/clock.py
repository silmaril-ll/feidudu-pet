"""肥嘟嘟看的钟：打招呼、晚上犯困都按它。时区在 config.TIMEZONE 里设，默认跟系统时间。"""
import datetime

from .config import TIMEZONE

_warned = False


def now():
    global _warned
    if TIMEZONE is None:
        return datetime.datetime.now()
    try:
        if isinstance(TIMEZONE, (int, float)):
            tz = datetime.timezone(datetime.timedelta(hours=TIMEZONE))
        else:
            from zoneinfo import ZoneInfo
            tz = ZoneInfo(TIMEZONE)
        return datetime.datetime.now(tz)
    except Exception:                                   # 时区名字写错了、或者 Windows 上没装 tzdata
        if not _warned:
            _warned = True
            print(f"时区 {TIMEZONE!r} 用不了，先按系统时间", flush=True)
        return datetime.datetime.now()


# (从几点开始, 说哪句)，按时间顺序
GREETINGS = ((5, "morning"), (11, "noon"), (14, "afternoon"), (18, "evening"), (23, "late"))


def greeting():
    """现在该说哪句：早呀 / 中午好 / 下午好 / 晚上好 / 夜深啦。"""
    hour = now().hour
    word = GREETINGS[-1][1]                             # 0 点到 5 点也是“夜深啦”
    for start, name in GREETINGS:
        if hour >= start:
            word = name
    return word
