import abc
import random
from typing import Any, final, override

from cellcrawler.character.character import Character, CharacterCommand
from cellcrawler.character.commands import ProceduralMovement, WrapInAttack
from cellcrawler.core.roguelike_calc_tree import CharacterNode, MobNextCell, NextCellContext
from cellcrawler.lib.base import DependencyInjector
from cellcrawler.maze.maze_data import MazeData

type CellPos = tuple[int, int]


class MobStrategy(abc.ABC):
    @abc.abstractmethod
    def make_command(self, mob: Character[Any]) -> CharacterCommand | None: ...


@final
class ChainMobStrategy(MobStrategy):
    def __init__(self, *strategies: MobStrategy) -> None:
        super().__init__()
        self.strategies = strategies

    @override
    def make_command(self, mob: Character[Any]) -> CharacterCommand | None:
        for s in self.strategies:
            if command := s.make_command(mob):
                return command
        return None


class MobMovementStrategy(MobStrategy, abc.ABC):
    @abc.abstractmethod
    def next_cell(self, current_cell: CellPos, maze: MazeData) -> CellPos | None: ...

    @override
    def make_command(self, mob: Character[Any]) -> CharacterCommand | None:
        maze = DependencyInjector.get(MazeData)
        next_cell = self.next_cell(mob.get_cell_pos(), maze)
        if not next_cell:
            return None
        return ProceduralMovement(next_cell)


@final
class CalcTreeMovementOverride(MobMovementStrategy):
    def __init__(self, base_strategy: MobMovementStrategy, node: CharacterNode):
        self.base_strategy = base_strategy
        self.calc_node = node

    @override
    def next_cell(self, current_cell: CellPos, maze: MazeData) -> CellPos | None:
        cell = self.base_strategy.next_cell(current_cell, maze)
        return self.calc_node.calculate(MobNextCell, cell, NextCellContext(current_cell))


@final
class StandStillStrategy(MobMovementStrategy):
    @override
    def next_cell(self, current_cell: CellPos, maze: MazeData) -> CellPos | None:
        return None


@final
class AfterBarStrategy(MobMovementStrategy):
    AFK_CHANCE = 0  # 0.15

    @override
    def next_cell(self, current_cell: CellPos, maze: MazeData) -> CellPos | None:
        x, y = current_cell
        options = maze.get_adjacent(x, y)
        if options and random.random() < 1 - self.AFK_CHANCE:
            return random.choice(options)
        return None


@final
class AttackStrategy(MobStrategy):
    def __init__(self, other: MobStrategy) -> None:
        super().__init__()
        self.other = other

    @override
    def make_command(self, mob: Character[Any]) -> CharacterCommand | None:
        if not (cmd := self.other.make_command(mob)):
            return None
        return WrapInAttack(mob, cmd)
