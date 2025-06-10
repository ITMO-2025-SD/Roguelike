from typing import Any, Generic

from typing_extensions import TypeVar

from cellcrawler.lib.calculation_tree import MathTarget, Node, RootNode

GN_co = TypeVar("GN_co", bound="GameNode[Any]", default="GameNode[Any]", covariant=True)


class GameNode(Node[GN_co, "LevelTree"], Generic[GN_co]):
    pass


class LevelTree(GameNode["LevelTree"], RootNode["LevelTree"]):  # pyright: ignore[reportUnsafeMultipleInheritance]
    def __init__(self):
        # https://github.com/microsoft/pyright/issues/10296
        RootNode.__init__(self)  # pyright: ignore[reportUnknownMemberType]


class CharacterNode(GameNode[LevelTree]):
    pass


class PlayerNode(CharacterNode):
    pass


CharacterSpeed = MathTarget[float, CharacterNode]("CharacterSpeed")
