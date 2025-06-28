from typing import Any, final, override

from direct.task.Task import TaskManager
from panda3d.core import NodePath

from cellcrawler.core.roguelike_calc_tree import (
    CharacterNode,
    DamageContext,
    DamageDealt,
    GameNode,
    MobNextCell,
    NextCellContext,
    PlayerNode,
)
from cellcrawler.inventory.datastore import InventoryItem, ItemCategory
from cellcrawler.lib.base import DependencyInjector
from cellcrawler.lib.model_repository import models


def make_timed(node: GameNode[Any], dur: float) -> None:
    task_mgr = DependencyInjector.get(TaskManager)
    task_mgr.do_method_later(dur, lambda _t: node.destroy(), f"timed-{id(node)}")  # pyright: ignore[reportUnknownLambdaType, reportUnknownArgumentType]


@final
class Stun(GameNode[CharacterNode]):
    def __init__(self, parent: CharacterNode, duration: float):
        super().__init__(parent)
        self.add_math_target(MobNextCell, self.get_next_cell)
        make_timed(self, duration)

    def get_next_cell(self, value: tuple[int, int] | None, ctx: NextCellContext):
        if ctx.mob is not self.parent:
            return value
        return ctx.start_pos


@final
class StunningArmor(InventoryItem):
    """Placeholder item."""

    def __init__(self):
        super().__init__(ItemCategory.ARMOR)

    @override
    def make_geom(self) -> NodePath:
        return models.get_item("stunning_chestplate")

    @override
    def make_equipment(self, parent: PlayerNode) -> GameNode[PlayerNode]:
        node = GameNode(parent)

        def stun(ctx: DamageContext):
            if ctx.attacker is parent:
                Stun(ctx.target, ctx.damage / 20)

        node.accept(DamageDealt, stun)
        return node
