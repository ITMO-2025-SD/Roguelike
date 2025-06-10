from typing import final, override

from panda3d.core import NodePath

from cellcrawler.core.roguelike_calc_tree import CharacterNode, CharacterSpeed, GameNode, PlayerNode
from cellcrawler.inventory.datastore import InventoryItem, ItemCategory
from cellcrawler.lib.model_repository import models


@final
class SpeedAmulet(InventoryItem):
    """Placeholder item."""

    def __init__(self):
        super().__init__(ItemCategory.AMULET)

    @override
    def make_geom(self) -> NodePath:
        return models.get_item("speed_amulet")

    @override
    def make_equipment(self, parent: PlayerNode) -> GameNode[PlayerNode]:
        node = GameNode(parent)

        def recalc_speed(value: float, character: CharacterNode):
            if character is node.parent:
                value *= 1.5
            return value

        node.add_math_target(CharacterSpeed, recalc_speed)
        return node
