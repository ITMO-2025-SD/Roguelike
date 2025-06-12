from collections.abc import Callable
from typing import final, override

from cellcrawler.character.mob import Mob
from cellcrawler.character.mob_factory import MobFactory
from cellcrawler.character.mob_strategy import AfterBarStrategy, CalcTreeMovementOverride, MobStrategy
from cellcrawler.character.mobs.doppelganger import Doppelganger
from cellcrawler.core.environment import Environment


@final
class StandardMobFactory(MobFactory):
    @override
    def get_constructor(self) -> Callable[[Environment], Mob]:
        return Doppelganger

    @override
    def get_default_strategy(self, mob: Mob) -> MobStrategy:
        return CalcTreeMovementOverride(AfterBarStrategy(), mob.calc_node)
