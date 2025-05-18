from cellcrawler.level.level_manager import LevelManager
from cellcrawler.lib.base import CrawlerBase, DependencyInjector
from cellcrawler.maze.standard_block_factory import StandardBlockFactory

base = CrawlerBase()
DependencyInjector.set_block_factory(StandardBlockFactory())
level_mgr = LevelManager()
level_mgr.next_floor()
base.run()
