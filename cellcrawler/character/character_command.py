import abc
import math
from collections.abc import Callable, Collection
from enum import Enum, auto
from typing import final, override

from panda3d.core import NodePath, Vec3


class CommandType(Enum):
    MOVE = auto()
    ROTATE = auto()


AdjusterT = Callable[[Vec3, NodePath], Vec3]


class CharacterCommand(abc.ABC):
    @abc.abstractmethod
    def run(self, character: NodePath, dt: float) -> None:
        pass


Forward = Vec3(0, 1, 0)
Back = Vec3(0, -1, 0)
Left = Vec3(-1, 0, 0)
Right = Vec3(1, 0, 0)


def adjustForHpr(point: Vec3, character: NodePath):
    x, y, z = point
    h = character.get_h()
    hRad = h * math.pi / 180
    return Vec3(-y * math.sin(hRad) + x * math.cos(hRad), y * math.cos(hRad) + x * math.sin(hRad), z)


@final
class MovementCommand(CharacterCommand):
    SPEED = 1000

    def __init__(self, delta: Callable[[], Vec3], adjuster: AdjusterT | None = None) -> None:
        super().__init__()
        self.delta = delta
        self.adjuster = adjuster

    @override
    def run(self, character: NodePath, dt: float):
        pos = character.get_pos()
        delta = self.delta() if self.adjuster is None else self.adjuster(self.delta(), character)
        character.set_pos(pos + delta * dt * self.SPEED)


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
    ROTATION_SPEED = 100000

    def __init__(self, direction: int):
        super().__init__()
        self.delta = direction

    @override
    def run(self, character: NodePath, dt: float):
        h = character.get_h()
        character.set_h(h + self.delta * dt * self.ROTATION_SPEED)
