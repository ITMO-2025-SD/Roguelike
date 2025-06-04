import abc
import math
from collections.abc import Callable, Collection
from enum import Enum, auto
from typing import final, override

from panda3d.core import NodePath, Vec3

from cellcrawler.core.roguelike_calc_tree import CharacterNode, CharacterSpeed


class CommandType(Enum):
    MOVE = auto()
    ROTATE = auto()


AdjusterT = Callable[[Vec3, NodePath], Vec3]


class CharacterCommand(abc.ABC):
    @abc.abstractmethod
    def run(self, character: NodePath, node: CharacterNode, dt: float) -> None:
        pass


Forward = Vec3(0, 1, 0)
Back = Vec3(0, -1, 0)
Left = Vec3(-1, 0, 0)
Right = Vec3(1, 0, 0)


def adjust_for_hpr(point: Vec3, character: NodePath):
    x, y, z = point
    h = character.get_h()
    h_rad = h * math.pi / 180
    return Vec3(-y * math.sin(h_rad) + x * math.cos(h_rad), y * math.cos(h_rad) + x * math.sin(h_rad), z)


@final
class MovementCommand(CharacterCommand):
    SPEED = 2000

    def __init__(self, delta: Callable[[], Vec3], adjuster: AdjusterT | None = None) -> None:
        super().__init__()
        self.delta = delta
        self.adjuster = adjuster

    def calc_speed(self, node: CharacterNode):
        return node.calculate(CharacterSpeed, self.SPEED, node)

    @override
    def run(self, character: NodePath, node: CharacterNode, dt: float):
        pos = character.get_pos()
        delta = self.delta() if self.adjuster is None else self.adjuster(self.delta(), character)
        character.set_pos(pos + delta * dt * self.calc_speed(node))


@final
class CompositeDelta:
    def __init__(self, vectors: Collection[Vec3]):
        self.vectors = vectors

    def __call__(self) -> Vec3:
        total = sum(self.vectors, Vec3(0, 0, 0))
        if total.dot(total) > 1:
            total.normalize()

        return total


@final
class RotationCommand(CharacterCommand):
    ROTATION_SPEED = 70000

    def __init__(self, direction: int):
        super().__init__()
        self.delta = direction

    @override
    def run(self, character: NodePath, node: CharacterNode, dt: float):
        h = character.get_h()
        character.set_h(h + self.delta * dt * self.ROTATION_SPEED)
