"""小卖部和衣柜：用捡来的花肥（便便）换东西。右键菜单里的「小卖部」「衣柜」都是这里加的。

货架在 art-source/items.js（饰品、叶子、价钱、抽到的机会），改完跑一次 runpet.py，这里自己会读到。
存档里：save["frass"] 花肥、save["owned"] 买过的饰品、save["wearing"] 正戴着的。
"""
import random

from . import effects
from .behaviors.munch import refuse_reason
from .lang import tr
from .menu import add_submenu
from .save import write_save


def add_to_menu(menu, pet):
    sp, frass = pet.sp, pet.save.get("frass", 0)
    shop = add_submenu(menu, tr(f"小卖部（花肥 {frass} 颗）", f"Shop ({frass} frass)"))
    price = sp.shop["gacha_price"]
    action = shop.addAction(tr(f"抽一片神秘叶子（{price} 颗）", f"Mystery leaf ({price} frass)"), lambda *_: buy_leaf(pet))
    action.setEnabled(frass >= price)
    shop.addSeparator()
    owned = pet.save.get("owned", [])
    for name, acc in sp.accessories.items():
        have = name in owned
        cost = tr("买过了", "owned") if have else tr(f"{acc['price']} 颗", f"{acc['price']} frass")
        action = shop.addAction(tr(f"{acc['label']}（{cost}）", f"{acc['label']} ({cost})"),
                                lambda *_, n=name: buy_accessory(pet, n))
        action.setEnabled(not have and frass >= acc["price"])

    if sp.toys:                                                 # 玩具：买一次永久拥有（toys.py）
        shop.addSeparator()
        have_toys = pet.save.get("toys", [])
        for name, toy in sp.toys.items():
            have = name in have_toys
            cost = tr("买过了", "owned") if have else tr(f"{toy['price']} 颗", f"{toy['price']} frass")
            action = shop.addAction(tr(f"{toy['label']}（{cost}）", f"{toy['label']} ({cost})"),
                                    lambda *_, n=name: buy_toy(pet, n))
            action.setEnabled(not have and frass >= toy["price"])

    mine = [n for n in owned if n in sp.accessories]           # 货架上撤掉的饰品就不显示了
    if mine:
        closet = add_submenu(menu, tr("衣柜", "Wardrobe"))
        wearing = pet.save.get("wearing")
        for name in mine:
            action = closet.addAction(sp.accessories[name]["label"], lambda *_, n=name: wear(pet, n))
            action.setCheckable(True)
            action.setChecked(name == wearing)
        closet.addSeparator()
        closet.addAction(tr("什么都不戴", "Nothing"), lambda *_: wear(pet, None))


def pay(pet, price):
    pet.save["frass"] = pet.save.get("frass", 0) - price


def buy_leaf(pet):
    """抽一片：按 items.js 里的 weight 随机，买了马上吃。"""
    price = pet.sp.shop["gacha_price"]
    if pet.save.get("frass", 0) < price:
        return
    reason = refuse_reason(pet)                 # 睡着、吃饱了、在墙上吊着的时候吃不了，也不扣花肥
    if reason:
        return pet.say(reason, 1.8)
    pool = [(name, leaf["weight"]) for name, leaf in pet.sp.leaves.items() if leaf["weight"] > 0]
    if not pool:
        return
    names, weights = zip(*pool)
    kind = random.choices(names, weights)[0]
    if effects.refuses(pet, pet.sp.leaves[kind]):   # 抽到枫叶：它才不吃，花肥也不扣
        return
    pay(pet, price)
    write_save(pet.save)
    pet.start("munch", leaf=kind)


def buy_accessory(pet, name):
    acc = pet.sp.accessories[name]
    if pet.save.get("frass", 0) < acc["price"] or name in pet.save.get("owned", []):
        return
    pay(pet, acc["price"])
    pet.save.setdefault("owned", []).append(name)
    wear(pet, name)


def wear(pet, name):
    pet.save["wearing"] = name
    write_save(pet.save)
    pet.update()
    if name:
        pet.say("pretty", 1.8)


def wearing_layer(pet, anim):
    """正戴着的饰品在这个动作里的画面（没戴、或者这个动作没有饰品画面，就是 None）。"""
    acc = pet.sp.accessories.get(pet.save.get("wearing"))
    return acc["anims"].get(anim) if acc else None


def buy_toy(pet, name):
    """买一样玩具：永久的，买了就在右键「玩具箱」里。"""
    toy = pet.sp.toys[name]
    if pet.save.get("frass", 0) < toy["price"] or name in pet.save.get("toys", []):
        return
    pay(pet, toy["price"])
    pet.save.setdefault("toys", []).append(name)
    write_save(pet.save)
    pet.say("play", 1.8)
