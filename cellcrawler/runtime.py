from cellcrawler.character.standard_mob_factory import StandardMobFactory
from cellcrawler.level.level_manager import LevelManager
from cellcrawler.lib.base import CrawlerBase, DependencyInjector
from cellcrawler.lib.model_repository import models
from cellcrawler.maze.standard_block_factory import StandardBlockFactory

base = CrawlerBase()
DependencyInjector.set_block_factory(StandardBlockFactory())
models.init()
level_mgr = LevelManager(StandardMobFactory())
level_mgr.next_floor()
base.run()
