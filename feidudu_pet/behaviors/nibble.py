"""自己啃一口：闲着的时候偶尔在叶子边（其实是屏幕上）啃一小口，过一会儿拉一颗便便。
很少发生（config.NIBBLE_WEIGHT），吃饱了、晚上不会啃，也不算一顿饭。"""
from . import register
from .base import Behavior
from .munch import is_full
from .sleep import is_night
from ..config import NIBBLE_WEIGHT
from ..save import write_save

CHEWS = 12                  # 嚼几下


@register
class Nibble(Behavior):
    name = "nibble"
    anim = "munch"
    frame_every = 2
    duration = None

    def weight_for(self, pet):
        if pet.surface != "floor" or is_full(pet) or is_night():
            return 0
        return NIBBLE_WEIGHT

    def tick(self, pet):
        if pet.tick >= CHEWS * self.frame_every:
            pet.save["gut"] = pet.save.get("gut", 0) + 1
            write_save(pet.save)
            pet.start("idle", 4)

    def under(self, pet, index):
        return pet.sp.leaves["citrus"]["frames"][3]             # 一小块快啃完的叶子
