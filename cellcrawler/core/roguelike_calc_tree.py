from dataclasses import dataclass
from typing import Any, Generic, final

from typing_extensions import TypeVar

from cellcrawler.lib.calculation_tree import MathTarget, Node, RootNode, Trigger
from cellcrawler.maze.pathfinding.pathfinding import PathfindingService

GN_co = TypeVar("GN_co", bound="GameNode[Any]", default="GameNode[Any]", covariant=True)


class GameNode(Node[GN_co, "LevelTree"], Generic[GN_co]):
    pass


class LevelTree(GameNode["LevelTree"], RootNode["LevelTree"]):  # pyright: ignore[reportUnsafeMultipleInheritance]
    def __init__(self):
        # https://github.com/microsoft/pyright/issues/10296
        RootNode.__init__(self)  # pyright: ignore[reportUnknownMemberType]


class CharacterNode(GameNode[LevelTree]):
    pass


@final
class PlayerNode(CharacterNode):
    def __init__(self, parent: LevelTree, pathfinding: PathfindingService):
        super().__init__(parent)
        self.pathfinding = pathfinding


@dataclass
class NextCellContext:
    mob: CharacterNode
    start_pos: tuple[int, int]


@dataclass
class DamageContext:
    attacker: CharacterNode
    target: CharacterNode
    damage: int


CharacterSpeed = MathTarget[float, CharacterNode]("CharacterSpeed")
MobNextCell = MathTarget[tuple[int, int] | None, NextCellContext]("MobNextCell")
MaxHealth = MathTarget[int, CharacterNode]("MaxHealth")
Damage = MathTarget[int, DamageContext]("Damage")
DamageDealt = Trigger[DamageContext]("DamageDealt")
MobDied = Trigger[()]("MobDied")
PlayerDied = Trigger[()]("PlayerDied")
