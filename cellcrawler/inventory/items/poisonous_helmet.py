import abc
from typing import Any, final, override

from direct.task.Task import Task, TaskManager
from panda3d.core import NodePath

from cellcrawler.character.character import AttackContext, AttackHappened, Character
from cellcrawler.core.roguelike_calc_tree import (
    CharacterNode,
    GameNode,
    PlayerNode,
)
from cellcrawler.inventory.datastore import InventoryItem, ItemCategory
from cellcrawler.lib.base import DependencyInjector
from cellcrawler.lib.model_repository import models


def make_timed(node: GameNode[Any], dur: float) -> None:
    task_mgr = DependencyInjector.get(TaskManager)
    task_mgr.do_method_later(dur, lambda _t: node.destroy(), f"timed-{id(node)}")  # pyright: ignore[reportUnknownLambdaType, reportUnknownArgumentType]


class SpreadableEffect(GameNode[CharacterNode], abc.ABC):
    def __init__(self, parent: CharacterNode):
        super().__init__(parent)
        self.accept(AttackHappened, self.do_clone)

    def do_clone(self, ctx: AttackContext):
        if ctx.attacker.calc_node is not self.parent:
            return
        # Prototype pattern.
        self.clone(ctx.defender)

    @abc.abstractmethod
    def clone(self, target: Character[Any]) -> object: ...


@final
class Poison(SpreadableEffect):
    def __init__(self, character: Character[Any], duration: float, damage: int):
        super().__init__(character.calc_node)
        self.character = character
        self.duration = duration
        self.damage = damage
        make_timed(self, duration)

        task_mgr = DependencyInjector.get(TaskManager)
        task_mgr.do_method_later(0.6, self.deal_damage, f"poison-{id(self)}")

    def deal_damage(self, task: Task):
        if self.destroyed:
            return None
        self.character.set_attacked(self.damage)
        return task.again

    @override
    def clone(self, target: Character[Any]) -> object:
        return Poison(target, self.duration, self.damage)


@final
class PoisonousHelmet(InventoryItem):
    """Placeholder item."""

    def __init__(self):
        super().__init__(ItemCategory.ARMOR)

    @override
    def make_geom(self) -> NodePath:
        return models.get_item("poisonous_helmet")

    @override
    def make_equipment(self, parent: PlayerNode) -> GameNode[PlayerNode]:
        node = GameNode(parent)

        def stun(ctx: AttackContext):
            if ctx.attacker.calc_node is parent:
                Poison(ctx.defender, 6.0, 3)

        node.accept(AttackHappened, stun)
        return node
