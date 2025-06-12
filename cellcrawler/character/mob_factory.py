import abc
from collections.abc import Callable

from cellcrawler.character.mob import Mob
from cellcrawler.character.mob_strategy import MobStrategy
from cellcrawler.core.environment import Environment


class MobFactory(abc.ABC):
    @abc.abstractmethod
    def get_constructor(self) -> Callable[[Environment], Mob]:
        pass

    @abc.abstractmethod
    def get_default_strategy(self, mob: Mob) -> MobStrategy:
        pass

    def create(self, env: Environment):
        mob = self.get_constructor()(env)
        if not mob.strategy:
            mob.set_strategy(self.get_default_strategy(mob))
        return mob
