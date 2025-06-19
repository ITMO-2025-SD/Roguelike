import abc
import random
from typing import final, override

from cellcrawler.character.character import CharacterCommand
from cellcrawler.character.commands import ProceduralMovement
from cellcrawler.core.roguelike_calc_tree import CharacterNode, MobNextCell, NextCellContext
from cellcrawler.lib.base import DependencyInjector
from cellcrawler.maze.maze_data import MazeData

type CellPos = tuple[int, int]


class MobStrategy(abc.ABC):
    @abc.abstractmethod
    def make_command(self, current_cell: CellPos) -> CharacterCommand | None: ...


@final
class ChainMobStrategy(MobStrategy):
    def __init__(self, strategies: list[MobStrategy]) -> None:
        super().__init__()
        self.strategies = strategies

    @override
    def make_command(self, current_cell: CellPos) -> CharacterCommand | None:
        for s in self.strategies:
            if command := s.make_command(current_cell):
                return command
        return None


class MobMovementStrategy(MobStrategy, abc.ABC):
    @abc.abstractmethod
    def next_cell(self, current_cell: CellPos, maze: MazeData) -> CellPos | None: ...

    @override
    def make_command(self, current_cell: CellPos) -> CharacterCommand | None:
        maze = DependencyInjector.get(MazeData)
        next_cell = self.next_cell(current_cell, maze)
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
