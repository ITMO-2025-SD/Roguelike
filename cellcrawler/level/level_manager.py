import functools
from collections.abc import Callable, Sequence
from typing import Final, final, override

from cellcrawler.character.mob_factory import MobFactory
from cellcrawler.character.player import Player
from cellcrawler.core.environment import Environment
from cellcrawler.core.roguelike_calc_tree import LevelTree, PlayerDied
from cellcrawler.gui.keybind_panel import KeybindPanel
from cellcrawler.level.mob_manager import MobManager, SpawnBlackboard
from cellcrawler.level.random_init_spawn_constructor import random_init_spawn_constructor
from cellcrawler.lib.base import DependencyInjector
from cellcrawler.lib.managed_node import ManagedNode
from cellcrawler.maze.const_level_factory import ConstLevelFactory
from cellcrawler.maze.level_factory import LevelFactory
from cellcrawler.maze.random_rooms_level_factory import RandomRoomsLevelFactory

type SpawnConstructor = Callable[[SpawnBlackboard], ManagedNode | None]


@final
class LevelManager(ManagedNode):
    PredeterminedLevels: Sequence[LevelFactory] = [ConstLevelFactory("maps/tutorial.ccw")]
    PredeterminedSpawns: Sequence[SpawnConstructor] = []

    @override
    def _cleanup(self) -> None:
        pass

    def __init__(self, mob_factory: MobFactory) -> None:
        super().__init__(None)
        self.level_num = 0
        self.keybind_panel = KeybindPanel(None)
        self.environ: Environment | None = None
        self.level_factory: LevelFactory | None = None
        self.mob_manager: MobManager | None = None
        self.mob_factory = mob_factory
        self.level_tree = LevelTree()
        DependencyInjector.set_level_tree(self.level_tree)
        self.player: Final = Player(self)
        self.pathfinding_started = False
        self.level_tree.accept(PlayerDied, self.destroy)

    def generate_floor(self, num: int) -> LevelFactory:
        return RandomRoomsLevelFactory(num + 10, 2, 3 + num // 4, num * (num + 1) + 4)

    def make_spawn_constructor(self, num: int) -> SpawnConstructor:
        # TODO: the architecture behind SpawnConstructors is not designed,
        # I tried to design it but failed, so kinda just went with whatever.
        return functools.partial(random_init_spawn_constructor, num * 3 + 1)

    def next_floor(self):
        # self.level_factory = self.generate_floor(self.level_num)
        # self.environ = self.level_factory.make_env()

        if self.level_num < len(self.PredeterminedLevels):
            self.level_factory = self.PredeterminedLevels[self.level_num]
        else:
            self.level_factory = self.generate_floor(self.level_num)
        if self.environ:
            self.environ.destroy()  # destroys mob manager and pathfinder too
        self.environ = self.level_factory.make_env(self, self.level_tree)
        self.environ.run_on_floor_end(self.next_floor)
        self.mob_manager = MobManager(self.environ)
        self.environ.spawn_player(self.player)
        if not self.pathfinding_started:
            self.pathfinding_started = True
            self.player.pathfinder_service.start()

        if self.level_num < len(self.PredeterminedSpawns):
            spawner_constructor = self.PredeterminedSpawns[self.level_num]
        else:
            spawner_constructor = self.make_spawn_constructor(self.level_num)
        blackboard = SpawnBlackboard(self.environ, self.mob_manager, self.mob_factory)
        spawner_constructor(blackboard)
        self.level_num += 1
