from dataclasses import dataclass

import pytest

from cellcrawler.lib.base import DependencyInjector
from cellcrawler.maze.maze_data import MazeCell, MazeData
from cellcrawler.maze.pathfinding.character_pathfinding import CharacterPathfinding


def test_bad_mazes():
    bad_mazes: list[list[list[MazeCell]]] = [
        [],  # height = 0
        [[]],  # width = 0
        [[MazeCell.OPEN, MazeCell.OPEN], [MazeCell.OPEN]],  # unevenly scaled
    ]

    for cells in bad_mazes:
        with pytest.raises(ValueError):
            MazeData(cells)


# ooooo
# o o o
# o   o
# oo oo
# o   o
# o   o
# ooooo
test_maze = MazeData(
    [
        [MazeCell.WALL, MazeCell.WALL, MazeCell.WALL, MazeCell.WALL, MazeCell.WALL],
        [MazeCell.WALL, MazeCell.OPEN, MazeCell.WALL, MazeCell.OPEN, MazeCell.WALL],
        [MazeCell.WALL, MazeCell.OPEN, MazeCell.OPEN, MazeCell.OPEN, MazeCell.WALL],
        [MazeCell.WALL, MazeCell.WALL, MazeCell.OPEN, MazeCell.WALL, MazeCell.WALL],
        [MazeCell.WALL, MazeCell.OPEN, MazeCell.OPEN, MazeCell.OPEN, MazeCell.WALL],
        [MazeCell.WALL, MazeCell.OPEN, MazeCell.OPEN, MazeCell.OPEN, MazeCell.WALL],
        [MazeCell.WALL, MazeCell.WALL, MazeCell.WALL, MazeCell.WALL, MazeCell.WALL],
    ]
)

DependencyInjector.set_maze(test_maze)


def test_adjacency():
    assert test_maze.get_adjacent(-20, -10) == []
    assert test_maze.get_adjacent(1, 1) == [(1, 2)]
    assert sorted(test_maze.get_adjacent(1, 2)) == [(1, 1), (2, 2)]


def test_pathfinding():
    @dataclass
    class FakePlayer:
        pos: tuple[int, int]

        def get_cell_pos(self):
            return self.pos

        def run_on_cell_change(self, _f: object):
            pass

    player = FakePlayer((1, 1))
    pathfinder = CharacterPathfinding(player)
    pathfinder.run()
    assert pathfinder.get_distance(1, 1) == 0
    assert pathfinder.get_distance(2, 5) == 5
    assert pathfinder.get_distance(1, 5) == 6
    assert pathfinder.get_distance(3, 5) == 6

    player.pos = (2, 5)
    pathfinder.run()
    assert pathfinder.get_distance(1, 1) == 5
    assert pathfinder.get_distance(2, 5) == 0
    assert pathfinder.get_distance(1, 5) == 1
    assert pathfinder.get_distance(3, 5) == 1
