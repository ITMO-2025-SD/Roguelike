import abc
from typing import override

from cellcrawler.character.character import Character
from cellcrawler.character.mob_strategy import MobStrategy
from cellcrawler.core.roguelike_calc_tree import CharacterNode, LevelTree
from cellcrawler.lib.managed_node import ManagedNode


class Mob(Character[CharacterNode], abc.ABC):
    def __init__(self, parent: ManagedNode | None) -> None:
        super().__init__(parent)
        self.strategy: MobStrategy | None = None

    def set_strategy(self, strategy: MobStrategy):
        self.strategy = strategy

    @override
    def create_calc_node(self, parent: LevelTree) -> CharacterNode:
        return CharacterNode(parent)
