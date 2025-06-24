import math
from collections.abc import Callable, Collection
from typing import Any, final, override

from direct.interval.FunctionInterval import Func, Wait
from direct.interval.Interval import Interval
from direct.interval.LerpInterval import LerpColorInterval
from direct.interval.MetaInterval import Sequence
from panda3d.core import NodePath, Vec3
from panda3d.direct import CInterval

from cellcrawler.character.character import (
    BEAM_ACTIVE_COLOR,
    BEAM_INACTIVE_COLOR,
    Character,
    CharacterCommand,
    characters,
)
from cellcrawler.core.roguelike_calc_tree import CharacterNode, CharacterSpeed
from cellcrawler.maze.blockpos_utils import maze_to_world_position

AdjusterT = Callable[[Vec3, NodePath], Vec3]


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
    SPEED = 6

    def __init__(self, delta: Callable[[], Vec3], adjuster: AdjusterT | None = None) -> None:
        super().__init__()
        self.delta = delta
        self.adjuster = adjuster

    def calc_speed(self, node: CharacterNode):
        return node.calculate(CharacterSpeed, self.SPEED, node)

    @override
    def run(self, character: Character[Any], dt: float):
        pos = character.node.get_pos()
        delta = self.delta() if self.adjuster is None else self.adjuster(self.delta(), character.node)
        character.node.set_pos(pos + delta * dt * self.calc_speed(character.calc_node))


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
    ROTATION_SPEED = 150

    def __init__(self, direction: int):
        super().__init__()
        self.delta = direction

    @override
    def run(self, character: Character[Any], dt: float):
        h = character.node.get_h()
        character.node.set_h(h + self.delta * dt * self.ROTATION_SPEED)


@final
class ProceduralMovement(CharacterCommand):
    ROTATION_CUTOFF = 0.02
    MOVEMENT_CUTOFF = 0.02
    MOVEMENT_SPEED = MovementCommand.SPEED // 4
    ROTATION_SPEED = RotationCommand.ROTATION_SPEED * 3 // 4

    def __init__(self, target_pos: tuple[int, int]) -> None:
        super().__init__()
        self.x, self.y = target_pos

    @override
    def run(self, character: Character[Any], dt: float) -> None:
        forward_vec = character.node.get_quat().get_forward()
        pos = character.node.get_pos()
        target_pos = maze_to_world_position(self.x, self.y)
        target_vec = Vec3(target_pos - pos)
        if target_vec.length() < self.MOVEMENT_CUTOFF:
            self.set_done()
            return
        target_vec[2] = forward_vec[2] = 0
        target_vec.normalize()
        rot_angle = target_vec.angle_rad(forward_vec.normalized())
        if rot_angle > self.ROTATION_CUTOFF:
            character.node.set_h(character.node.get_h() + dt * self.ROTATION_SPEED)
        elif rot_angle < -self.ROTATION_CUTOFF:
            character.node.set_h(character.node.get_h() - dt * self.ROTATION_SPEED)
        else:
            character.node.set_pos(pos + target_vec * self.MOVEMENT_SPEED * dt)


@final
class IntervalCommand(CharacterCommand):
    def __init__(self, interval: Interval | CInterval) -> None:
        super().__init__()
        # types-panda3d bug, too lazy to fix.
        self.interval = Sequence(interval, Func(self.set_done))  # pyright: ignore[reportCallIssue]
        self.started = False

    @override
    def run(self, character: Character[Any], dt: float) -> None:
        if not self.started:
            self.interval.start()
            self.started = True


ATTACK_WINDUP_TIME = 0.06
ATTACK_ACTIVE_TIME = 0.1
ATTACK_SLOWDOWN_TIME = 0.54


def make_attack(attacker: Character[Any]) -> CharacterCommand | None:
    if attacker.attacking_beam is None:
        return None

    def attack():
        for char in characters.collisions.get_attacked_chars(attacker):
            attacker.attack(char)

    return IntervalCommand(
        Sequence(  # pyright: ignore[reportCallIssue]
            LerpColorInterval(attacker.attacking_beam, ATTACK_WINDUP_TIME, BEAM_ACTIVE_COLOR),
            Func(attack),
            Wait(ATTACK_ACTIVE_TIME),
            LerpColorInterval(attacker.attacking_beam, ATTACK_SLOWDOWN_TIME, BEAM_INACTIVE_COLOR),
        )
    )
