from typing import final

from cellcrawler.core.environment import Environment
from cellcrawler.maze.const_level_factory import ConstLevelFactory
from cellcrawler.maze.level_factory import LevelFactory


@final
class LevelManager:
    PredeterminedLevels = [ConstLevelFactory("maps/tutorial.ccw")]

    def __init__(self) -> None:
        self.level_num = 0
        self.environ: Environment | None = None
        self.level_factory: LevelFactory | None = None

    def generate_floor(self, num: int) -> LevelFactory:
        raise NotImplementedError(f"generate_floor: {num}")

    def next_floor(self):
        if self.level_num < len(self.PredeterminedLevels):
            self.level_factory = self.PredeterminedLevels[self.level_num]
        else:
            self.level_factory = self.generate_floor(self.level_num)
        if self.environ:
            self.environ.destroy()
        self.environ = self.level_factory.make_env()
        self.level_num += 1
