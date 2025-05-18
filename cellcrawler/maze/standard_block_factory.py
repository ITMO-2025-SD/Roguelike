from typing import override

from direct.showbase.Loader import Loader
from panda3d.core import NodePath

from cellcrawler.lib.base import inject_globals
from cellcrawler.lib.managed_node import ManagedNodePath
from cellcrawler.maze.block_factory import BlockFactory


class StandardBlockFactory(BlockFactory):
    @override
    def _create_empty(self) -> NodePath | ManagedNodePath | None:
        return None

    @override
    @inject_globals
    def _create_wall(self, loader: Loader) -> NodePath | ManagedNodePath | None:
        return loader.load_model("world/wall.bam", okMissing=False)
