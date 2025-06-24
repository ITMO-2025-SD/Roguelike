import random
from collections.abc import Callable
from typing import final, override

from panda3d.core import NodePath

from cellcrawler.character.mob import Mob
from cellcrawler.character.player import Player
from cellcrawler.core.roguelike_calc_tree import LevelTree, MobDied, PlayerDied
from cellcrawler.lib.base import DependencyInjector, RootNodes, inject_globals
from cellcrawler.lib.managed_node import ManagedNodePath
from cellcrawler.maze.block_factory import BlockFactory
from cellcrawler.maze.blockpos_utils import MAZE_SCALE, maze_to_world_position
from cellcrawler.maze.maze_data import MazeCell, MazeData


@final
class Environment(ManagedNodePath):
    def __init__(self, maze: MazeData) -> None:
        self.maze = maze
        self.open_positions = [
            (x, y) for x in range(maze.width) for y in range(maze.height) if maze.cells[y][x] == MazeCell.OPEN
        ]
        super().__init__(None)
        self.calc_node = LevelTree()
        self.mob_count = 0
        self.calc_node.accept(MobDied, self.mob_died)
        self.calc_node.accept(PlayerDied, self.player_died)
        self._on_floor_end_callback: Callable[[], None] | None = None

    def mob_died(self):
        self.mob_count -= 1
        if not self.mob_count and self._on_floor_end_callback:
            self._on_floor_end_callback()

    def player_died(self):
        raise RuntimeError("death screen not yet implemented")

    def run_on_floor_end(self, callback: Callable[[], None]):
        self._on_floor_end_callback = callback

    @override
    @inject_globals
    def _load(self, factory: BlockFactory, nodes: RootNodes) -> NodePath:
        DependencyInjector.set_maze(self.maze)
        maze_np = NodePath("environment")
        for i, row in enumerate(self.maze.cells):
            for j, cell in enumerate(row):
                cell_node = factory.create(cell, MAZE_SCALE)
                if cell_node:
                    cell_node.set_pos(maze_to_world_position(j, i))
                    cell_node.reparent_to(maze_np)
        maze_np.reparent_to(nodes.render)
        return maze_np

    def choose_open_pos(self):
        return random.choice(self.open_positions)

    def spawn_player(self):
        player = Player(self)
        player.node.reparent_to(self.node)
        open_pos = self.choose_open_pos()
        self.maze.set_occupied(open_pos)
        player.node.set_pos(maze_to_world_position(*open_pos))
        return player

    def spawn_mob(self, mob: Mob):
        mob.node.reparent_to(self.node)
        self.mob_count += 1
