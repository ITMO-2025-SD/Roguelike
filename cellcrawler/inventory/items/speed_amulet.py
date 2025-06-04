from typing import final, override

from direct.showbase.Loader import Loader
from panda3d.core import NodePath

from cellcrawler.core.roguelike_calc_tree import CharacterNode, CharacterSpeed, GameNode, PlayerNode
from cellcrawler.inventory.datastore import InventoryItem, ItemCategory
from cellcrawler.lib.base import inject_globals


@final
class SpeedAmulet(InventoryItem):
    """Placeholder item."""

    def __init__(self):
        super().__init__(ItemCategory.AMULET)

    @override
    @inject_globals
    def make_geom(self, loader: Loader) -> NodePath:
        model = loader.load_model("gui/items.bam", okMissing=False)
        return model.find("**/speed_amulet")

    @override
    def make_equipment(self, parent: PlayerNode) -> GameNode[PlayerNode]:
        node = GameNode(parent)

        def recalc_speed(value: float, character: CharacterNode):
            if character is node.parent:
                value *= 1.5
            return value

        node.add_math_target(CharacterSpeed, recalc_speed)
        return node
