from typing import final, override

from panda3d.core import NodePath

from cellcrawler.core.roguelike_calc_tree import GameNode, MobNextCell, NextCellContext, PlayerNode
from cellcrawler.inventory.datastore import InventoryItem, ItemCategory
from cellcrawler.lib.model_repository import models


@final
class FearAmulet(InventoryItem):
    """Placeholder item."""

    MAX_FEAR_DISTANCE = 100

    def __init__(self):
        super().__init__(ItemCategory.AMULET)

    @override
    def make_geom(self) -> NodePath:
        return models.get_item("fear_amulet")

    @override
    def make_equipment(self, parent: PlayerNode) -> GameNode[PlayerNode]:
        node = GameNode(parent)

        def recalc_next_cell(value: tuple[int, int] | None, ctx: NextCellContext):
            distance_to_player = parent.pathfinding.get_distance(*ctx.start_pos)
            if distance_to_player is not None and distance_to_player <= self.MAX_FEAR_DISTANCE:
                adjacent_cells = parent.pathfinding.get_distances_to_adjacent(*ctx.start_pos)
                if not adjacent_cells or max(adjacent_cells)[0] < distance_to_player:
                    return None
                return max(adjacent_cells)[1]
            return value

        node.add_math_target(MobNextCell, recalc_next_cell)
        return node
