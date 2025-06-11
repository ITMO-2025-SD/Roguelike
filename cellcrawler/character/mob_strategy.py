import abc
import random
from typing import final, override

from cellcrawler.character.character_command import CharacterCommand, ProceduralMovement
from cellcrawler.lib.base import DependencyInjector
from cellcrawler.maze.maze_data import MazeData, is_visitable

type CellPos = tuple[int, int]


class MobStrategy(abc.ABC):
    @abc.abstractmethod
    def next_cell(self, current_cell: CellPos, maze: MazeData) -> CellPos | None: ...

    def make_command(self, current_cell: CellPos) -> CharacterCommand | None:
        maze = DependencyInjector.get(MazeData)
        next_cell = self.next_cell(current_cell, maze)
        if not next_cell:
            return None
        return ProceduralMovement(next_cell)


@final
class StandStillStrategy(MobStrategy):
    @override
    def next_cell(self, current_cell: CellPos, maze: MazeData) -> CellPos | None:
        return None


@final
class AfterBarStrategy(MobStrategy):
    AFK_CHANCE = 0  # 0.15

    @override
    def next_cell(self, current_cell: CellPos, maze: MazeData) -> CellPos | None:
        x, y = current_cell
        options: list[CellPos] = []
        if x > 0 and is_visitable(maze.cells[y][x - 1]):
            options.append((x - 1, y))
        if x + 1 < len(maze.cells[0]) and is_visitable(maze.cells[y][x + 1]):
            options.append((x + 1, y))
        if y > 0 and is_visitable(maze.cells[y - 1][x]):
            options.append((x, y - 1))
        if y + 1 < len(maze.cells) and is_visitable(maze.cells[y + 1][x]):
            options.append((x, y + 1))
        if options and random.random() < 1 - self.AFK_CHANCE:
            return random.choice(options)
        return None
