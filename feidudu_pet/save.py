"""存档：吃了几片叶子、长多胖、选的大小。"""
import json

from .config import DEFAULT_SIZE, SAVE_FILE


def load_save():
    try:
        data = json.loads(SAVE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {"growth": 1.0, "leaves": 0}
    if data.get("v", 1) < 2:                             # 旧存档：换成新的默认小尺寸
        data["size"] = DEFAULT_SIZE
        data["v"] = 2
    return data


def write_save(data):
    try:
        SAVE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError:
        pass                                             # 存不了就算了，不影响玩
