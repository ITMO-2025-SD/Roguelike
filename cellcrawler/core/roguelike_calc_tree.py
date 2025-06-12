from dataclasses import dataclass
from typing import Any, Generic, final

from typing_extensions import TypeVar

from cellcrawler.lib.calculation_tree import MathTarget, Node, RootNode
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
    start_pos: tuple[int, int]


CharacterSpeed = MathTarget[float, CharacterNode]("CharacterSpeed")
MobNextCell = MathTarget[tuple[int, int] | None, NextCellContext]("MobNextCell")
