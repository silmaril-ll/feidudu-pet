"""读 sprites 文件夹里的画面帧和对话泡泡。"""
import json
from dataclasses import dataclass

from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QIcon, QPixmap

from .config import SPRITES


@dataclass
class Anim:
    frames: list          # QPixmap 列表（2 倍图）
    anchor: QPointF       # 支点：地面动作是脚底中间，拎起来是捏住的地方，吊着是嘴巴
    bbox: QRectF          # 所有帧里真正有画的范围（逻辑像素，画面坐标）


class Sprites:
    def __init__(self):
        info = json.loads((SPRITES / "sprites.json").read_text(encoding="utf-8"))
        r = info["scale"]
        self.ratio = r
        self.anims = {}
        for name, a in info["anims"].items():
            x0, y0, x1, y1 = a["bbox"]
            self.anims[name] = Anim(
                frames=[self._load(f) for f in a["files"]],
                anchor=QPointF(a["anchor"][0] / r, a["anchor"][1] / r),
                bbox=QRectF(x0 / r, y0 / r, (x1 - x0) / r, (y1 - y0) / r),
            )
        self.bubbles = {name: self._load(f) for name, f in info["bubbles"].items()}
        self.frass = self._load(info["frass"])                    # 一颗便便
        # 小卖部（货架在 art-source/items.js）：饰品是每个动作上面的一层，叶子是吃的时候垫在下面的一层
        self.shop = info["shop"]
        #   这两种画面只存了有画的那一块：每帧是 (画面, 放在哪)
        self.accessories = {name: {"label": a["label"], "price": a["price"],
                                   "anims": {anim: [self._layer(f) for f in files] for anim, files in a["anims"].items()}}
                            for name, a in info["accessories"].items()}
        self.leaves = {name: dict(leaf, name=name, frames=[self._layer(f) for f in leaf["files"]])
                       for name, leaf in info["leaves"].items()}
        self.sparkles = [self._load(f) for f in info["sparkles"]]      # 金叶子：身边的小星星
        self.scents = [self._load(f) for f in info["scents"]]          # 芸香叶：飘起来的香味
        skin = info["skin"]                                       # 伪装用的输入法皮肤（见 disguise.py）
        self.skin = {
            "card": self._load(skin["file"]),
            "size": (skin["w"], skin["h"]),
            "cells": {name: QRectF(x0, y0, x1 - x0, y1 - y0) for name, (x0, y0, x1, y1) in zip(skin["order"], skin["cells"])},
            "pet": QRectF(skin["pet"][0], skin["pet"][1], skin["pet"][2] - skin["pet"][0], skin["pet"][3] - skin["pet"][1]),
            "glyphs": {name: self._load(f) for name, f in skin["glyphs"].items()},
        }
        # 程序图标：用 feidudu_icon.ico（启动器快捷方式也是它）；托盘图标在 tray.py 里直接画
        ico = SPRITES.parent / "feidudu_icon.ico"
        self.icon = QIcon(str(ico if ico.exists() else SPRITES / "icon.png"))
        crawl = self.anims["crawl"]
        # 身体从支点往前/往后伸多长（1 倍大小），用来算它贴墙、转角的位置
        self.half = max(crawl.anchor.x() - crawl.bbox.left(), crawl.bbox.right() - crawl.anchor.x())
        hang = self.anims["hang"]
        self.hang_len = hang.bbox.bottom() - hang.anchor.y()     # 嘴巴到尾巴

    def _layer(self, f):
        return self._load(f["file"]), QPointF(f["at"][0] / self.ratio, f["at"][1] / self.ratio)

    def _load(self, filename):
        pixmap = QPixmap(str(SPRITES / filename))
        pixmap.setDevicePixelRatio(self.ratio)
        return pixmap
