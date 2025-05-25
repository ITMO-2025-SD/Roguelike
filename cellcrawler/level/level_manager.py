from typing import final

from cellcrawler.character.player import Player
from cellcrawler.core.environment import Environment
from cellcrawler.gui.keybind_panel import KeybindPanel
from cellcrawler.maze.const_level_factory import ConstLevelFactory
from cellcrawler.maze.level_factory import LevelFactory
from cellcrawler.maze.random_dfs_level_factory import RandomDfsLevelFactory


@final
class LevelManager:
    PredeterminedLevels = [ConstLevelFactory("maps/tutorial.ccw")]

    def __init__(self) -> None:
        self.level_num = 0
        self.keybind_panel = KeybindPanel(None)
        self.environ: Environment | None = None
        self.level_factory: LevelFactory | None = None
        self.player: Player | None = None

    def generate_floor(self, num: int) -> LevelFactory:
        return RandomDfsLevelFactory(num)

    def next_floor(self):
        # self.level_factory = self.generate_floor(self.level_num)
        # self.environ = self.level_factory.make_env()

        if self.level_num < len(self.PredeterminedLevels):
            self.level_factory = self.PredeterminedLevels[self.level_num]
        else:
            self.level_factory = self.generate_floor(self.level_num)
        if self.environ:
            self.environ.destroy()
        self.environ = self.level_factory.make_env()
        self.player = self.environ.spawn_player()
        self.level_num += 1
