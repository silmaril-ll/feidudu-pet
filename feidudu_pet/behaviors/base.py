"""所有动作的共同样子。新动作继承 Behavior，按需要改下面这些。"""
from PyQt6.QtCore import QPointF

from .. import world


class Behavior:
    name = ""                  # 动作的名字（pet.state 就是它）
    anim = ""                  # 用 sprites.json 里哪组画面
    frame_every = 1            # 几拍换一帧（1 拍 = 90 毫秒）
    duration = (3, 8)          # 被随机挑中时做几秒；None 表示动作自己决定什么时候结束
    menu_order = 100           # 右键菜单里的顺序

    def weight_for(self, pet):
        """现在有多想做这个动作（0 = 不会被随机挑中）。"""
        return 0

    def enter(self, pet, **kw):
        """开始做这个动作。"""

    def tick(self, pet):
        """每一拍调用一次。"""

    def exit(self, pet):
        """换别的动作之前调用。"""

    def menu_items(self, pet):
        """往右键菜单里加的项：[(文字, 函数), ...]"""
        return []

    def under(self, pet, index):
        """垫在身体下面画的一层（比如正在吃的叶子）：(画面, 放在哪)，和身体同一个画法。没有就返回 None。"""
        return None

    def frame(self, pet):
        """画哪一帧：(画面组, 第几帧, 支点在屏幕上的位置, 旋转角度, 要不要镜像)。
        默认是地面动作：支点是脚底，跟着所在的面旋转。"""
        deg, mirrored = world.pose_transform(pet)
        return self.anim, pet.tick // self.frame_every, QPointF(pet.ax, pet.ay), deg, mirrored

    @property
    def on_ground(self):
        """是不是贴着一个面的动作（地上会画小影子）。"""
        return type(self).frame is Behavior.frame
