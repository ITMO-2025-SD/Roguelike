from typing import final, override

from panda3d.core import NodePath, Vec3

from cellcrawler.lib.base import DependencyInjector, RootNodes, inject_globals
from cellcrawler.lib.managed_node import ManagedNodePath
from cellcrawler.maze.block_factory import BlockFactory
from cellcrawler.maze.maze_data import MazeData


@final
class Environment(ManagedNodePath):
    SCALE = 1

    def __init__(self, maze: MazeData) -> None:
        self.maze = maze
        super().__init__(None)

    @override
    @inject_globals
    def _load(self, factory: BlockFactory, nodes: RootNodes) -> NodePath:
        DependencyInjector.set_maze(self.maze)
        maze_np = NodePath("environment")
        for i, row in enumerate(self.maze.cells):
            for j, cell in enumerate(row):
                cell_node = factory.create(cell, self.SCALE)
                if cell_node:
                    cell_node.set_pos(Vec3(i, j, 0) * self.SCALE)
                    cell_node.reparent_to(maze_np)
        maze_np.reparent_to(nodes.render)
        return maze_np
