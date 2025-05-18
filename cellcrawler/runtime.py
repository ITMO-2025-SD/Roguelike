from cellcrawler.level.level_manager import LevelManager
from cellcrawler.lib.base import CrawlerBase

base = CrawlerBase()
level_mgr = LevelManager()
level_mgr.next_floor()
base.run()
