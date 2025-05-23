import random
from typing import final, override

from panda3d.core import NodePath, Vec3

from cellcrawler.character.player import Player
from cellcrawler.lib.base import DependencyInjector, RootNodes, inject_globals
from cellcrawler.lib.managed_node import ManagedNodePath
from cellcrawler.maze.block_factory import BlockFactory
from cellcrawler.maze.maze_data import MazeCell, MazeData


@final
class Environment(ManagedNodePath):
    SCALE = 1

    def __init__(self, maze: MazeData) -> None:
        self.maze = maze
        self.open_positions = [
            (x, y) for x in range(maze.width) for y in range(maze.height) if maze.cells[y][x] == MazeCell.OPEN
        ]
        super().__init__(None)

    def __get_position(self, x: int, y: int):
        return Vec3(x, -y, 0) * self.SCALE

    @override
    @inject_globals
    def _load(self, factory: BlockFactory, nodes: RootNodes) -> NodePath:
        DependencyInjector.set_maze(self.maze)
        maze_np = NodePath("environment")
        for i, row in enumerate(self.maze.cells):
            for j, cell in enumerate(row):
                cell_node = factory.create(cell, self.SCALE)
                if cell_node:
                    cell_node.set_pos(self.__get_position(j, i))
                    cell_node.reparent_to(maze_np)
        maze_np.reparent_to(nodes.render)
        return maze_np

    def choose_open_pos(self):
        return random.choice(self.open_positions)

    def spawn_player(self):
        player = Player(self)
        player.node.reparent_to(self.node)
        player.node.set_pos(self.__get_position(*self.choose_open_pos()))
        return player
