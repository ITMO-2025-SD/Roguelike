import random
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
        self.color = (random.random(), random.random(), random.random(), 1)

    @override
    @inject_globals
    def make_geom(self, loader: Loader) -> NodePath:
        # TODO: this model is temporary
        model = loader.load_model("characters/player.bam", okMissing=False)
        model.set_color_scale(self.color)
        return model

    @override
    def make_equipment(self, parent: PlayerNode) -> GameNode[PlayerNode]:
        node = GameNode(parent)

        def recalc_speed(value: float, character: CharacterNode):
            if character is node.parent:
                value *= 1.5
            return value

        node.add_math_target(CharacterSpeed, recalc_speed)
        return node
