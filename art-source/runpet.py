"""Render every 肥嘟嘟 frame into ../sprites (same seeds, same result every time).

Needs: python -m pip install playwright pillow ; python -m playwright install chromium
Set CHROME_PATH to use a specific Chromium instead of Playwright's own.
"""
import asyncio, base64, io, json, os, time, urllib.request
from pathlib import Path
from playwright.async_api import async_playwright
from PIL import Image

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "sprites"
# 泡泡里的字：中文用龙藏体，英文用 Patrick Hand（都是 SIL Open Font License，第一次画的时候自动下载，不进仓库）
FONTS = {HERE / "LongCang.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/longcang/LongCang-Regular.ttf",
         HERE / "PatrickHand.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/patrickhand/PatrickHand-Regular.ttf"}


def save_png(url, path):
    data = base64.b64decode(url.split(",")[1])
    path.write_bytes(data)
    return Image.open(io.BytesIO(data)).getchannel("A").getbbox()


def save_cropped(url, path):
    """只存有画的那一块（饰品、叶子这种一层一层的画面，大部分是透明的），返回它在原画布上的左上角。
    这样读进程序里占的内存小很多。"""
    im = Image.open(io.BytesIO(base64.b64decode(url.split(",")[1])))
    box = im.getchannel("A").getbbox() or (0, 0, 1, 1)
    im.crop(box).save(path)
    return [box[0], box[1]]


async def main():
    for font, url in FONTS.items():
        if not font.exists():
            urllib.request.urlretrieve(url, font)
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("*.png"):
        old.unlink()
    async with async_playwright() as p:
        kw = {"args": ["--allow-file-access-from-files"]}
        if os.environ.get("CHROME_PATH"):
            kw["executable_path"] = os.environ["CHROME_PATH"]
        browser = await p.chromium.launch(**kw)
        page = await browser.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        await page.goto((HERE / "pet.html").as_uri())
        t = time.time()
        r = await page.evaluate("renderPet()")
        print("render s", round(time.time() - t, 1), errors)
        manifest = {"scale": r["scale"], "anims": {}, "bubbles": {}, "bubbles_en": {}}
        for name, a in r["anims"].items():
            files, box = [], None
            for i, url in enumerate(a["frames"]):
                fn = f"{name}_{i:02d}.png"
                b = save_png(url, OUT / fn)
                box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
                files.append(fn)
            manifest["anims"][name] = {"files": files, "anchor": a["anchor"], "w": a["w"], "h": a["h"], "bbox": list(box)}
        # 小卖部：饰品是每个动作的一层，叶子是 4 个咬了几口的样子（货架在 items.js）
        manifest["shop"] = r["shop"]
        manifest["accessories"] = {}
        for name, acc in r["accessories"].items():
            anims = {}
            for anim, frames in acc["anims"].items():
                anims[anim] = []
                for i, url in enumerate(frames):
                    fn = f"acc_{name}_{anim}_{i:02d}.png"
                    anims[anim].append({"file": fn, "at": save_cropped(url, OUT / fn)})
            manifest["accessories"][name] = {"label": acc["label"], "label_en": acc["label_en"], "price": acc["price"], "anims": anims}
        manifest["leaves"] = {}
        for name, leaf in r["leaves"].items():
            files = []
            for i, url in enumerate(leaf["frames"]):
                fn = f"leaf_{name}_{i}.png"
                files.append({"file": fn, "at": save_cropped(url, OUT / fn)})
            manifest["leaves"][name] = {k: v for k, v in leaf.items() if k != "frames"} | {"files": files}
        manifest["scents"] = []
        for i, url in enumerate(r["scents"]):
            save_png(url, OUT / f"scent_{i}.png")
            manifest["scents"].append(f"scent_{i}.png")
        manifest["sparkles"] = []
        for i, url in enumerate(r["sparkles"]):
            save_png(url, OUT / f"sparkle_{i}.png")
            manifest["sparkles"].append(f"sparkle_{i}.png")
        for name, url in r["bubbles"].items():
            fn = f"bubble_{name}.png"
            save_png(url, OUT / fn)
            manifest["bubbles"][name] = fn
        for name, url in r["bubbles_en"].items():                 # 英文版泡泡（LANGUAGE = "en"）
            fn = f"bubble_en_{name}.png"
            save_png(url, OUT / fn)
            manifest["bubbles_en"][name] = fn
        save_png(r["popper"], OUT / "popper.png")               # 礼花筒和彩纸（每吃满一百片叶子）
        manifest["popper"] = "popper.png"
        manifest["confetti"] = []
        for i, url in enumerate(r["confetti"]):
            save_png(url, OUT / f"confetti_{i:02d}.png")
            manifest["confetti"].append(f"confetti_{i:02d}.png")
        save_png(r["frass"], OUT / "frass.png")
        manifest["frass"] = "frass.png"
        skin = r["skin"]                                   # 伪装用的输入法皮肤
        save_png(skin["card"], OUT / "skin.png")
        glyphs = {}
        for name, url in skin["glyphs"].items():
            save_png(url, OUT / f"skin_{name}.png")
            glyphs[name] = f"skin_{name}.png"
        manifest["skin"] = {"file": "skin.png", "w": skin["w"], "h": skin["h"], "order": skin["order"],
                            "cells": skin["cells"], "pet": skin["pet"], "glyphs": glyphs}
        menu = r["menu"]                                   # 右键菜单的蜡笔皮肤
        for name in ("bg", "hover", "arrow", "check", "sep"):
            save_png(menu[name], OUT / f"menu_{name}.png")
        manifest["menu"] = {"cut": menu["cut"]}
        save_png(r["icon"], OUT / "icon.png")
        (OUT / "sprites.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
        await browser.close()


asyncio.run(main())
