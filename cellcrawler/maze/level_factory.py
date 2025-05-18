import abc

from cellcrawler.core.environment import Environment
from cellcrawler.maze.maze_data import MazeData


class LevelFactory(abc.ABC):
    @abc.abstractmethod
    def _make_level(self) -> MazeData:
        pass

    def make_env(self) -> Environment:
        return Environment(self._make_level())
