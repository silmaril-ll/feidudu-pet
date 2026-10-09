"""肥嘟嘟桌宠的程序都在这个文件夹里。启动入口是上一层的 feidudu.pyw。

自己想调的数字写在上一层的 my_config.py 里（和 feidudu.pyw 放在一起，没有就新建一个）：
只写想改的那几行，比如 AWAY_AFTER = 600，它会盖过 config.py 里同名的数字。
my_config.py 不进 git，所以 git pull 更新的时候不会和它冲突。
这里在别的文件读 config 之前先把它读进来，所以哪里用到这些数字都是改过的。"""
from . import config as _config

_mine = _config.ROOT / "my_config.py"           # utf-8-sig：记事本存的“带 BOM 的 UTF-8”也读得了
if _mine.exists():
    _values = {}
    exec(compile(_mine.read_text(encoding="utf-8-sig"), str(_mine), "exec"), _values)
    for _name, _value in _values.items():
        if _name.isupper():                    # 只认全大写的名字（config.py 里的数字都是这样）
            setattr(_config, _name, _value)
