"""界面用哪种语言：config.LANGUAGE，"zh" 中文（默认），"en" 英文。

菜单上的字在代码里写成 tr("中文", "English")；
泡泡、叶子和饰品的名字是画好的（art-source/pet.js 的 BUBBLES_EN、items.js 的 en），sprites.py 按语言挑。"""
from .config import LANGUAGE

EN = LANGUAGE == "en"


def tr(zh, en):
    return en if EN else zh
