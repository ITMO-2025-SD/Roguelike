import abc
from typing import Final, override

from panda3d.core import CollisionHandlerEvent

from cellcrawler.character.character import (
    MOB_BEAM_COLLIDE_MASK,
    PLAYER_BEAM_COLLIDE_MASK,
    PUSHER_COLLIDE_MASK,
    Character,
)
from cellcrawler.character.mob_strategy import MobStrategy
from cellcrawler.core.roguelike_calc_tree import CharacterNode, LevelTree
from cellcrawler.lib.managed_node import ManagedNode


class Mob(Character[CharacterNode], abc.ABC):
    @override
    def get_collision_handler(self) -> CollisionHandlerEvent:
        return self.collision_handler

    def __init__(self, parent: ManagedNode | None) -> None:
        # self.attacked_by_queue: Final = CollisionHandlerQueue()
        self.collision_handler: Final = CollisionHandlerEvent()
        super().__init__(parent)
        # QueueDebugger(self, f"mob {id(self)}", self.attacked_by_queue)
        self.strategy: MobStrategy | None = None
        self.collision_node.set_into_collide_mask(PUSHER_COLLIDE_MASK)
        self.collision_node.set_from_collide_mask(PLAYER_BEAM_COLLIDE_MASK)
        self.beam_collider.set_into_collide_mask(MOB_BEAM_COLLIDE_MASK)

    def set_strategy(self, strategy: MobStrategy):
        self.strategy = strategy

    @override
    def create_calc_node(self, parent: LevelTree) -> CharacterNode:
        return CharacterNode(parent)
