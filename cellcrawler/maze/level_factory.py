import abc

from cellcrawler.core.environment import Environment
from cellcrawler.core.roguelike_calc_tree import LevelTree
from cellcrawler.lib.managed_node import ManagedNode
from cellcrawler.maze.maze_data import MazeData


class LevelFactory(abc.ABC):
    @abc.abstractmethod
    def _make_level(self) -> MazeData:
        pass

    def make_env(self, parent: ManagedNode, level_tree: LevelTree) -> Environment:
        return Environment(parent, level_tree, self._make_level())
