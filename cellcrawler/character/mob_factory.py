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
    def get_strategy(self) -> MobStrategy:
        pass

    def create(self, env: Environment):
        mob = self.get_constructor()(env)
        mob.set_strategy(self.get_strategy())
        return mob
