from typing import override

from panda3d.core import NodePath

from cellcrawler.lib.managed_node import ManagedNodePath
from cellcrawler.maze.block_factory import BlockFactory


class StandardBlockFactory(BlockFactory):
    @override
    def _create_empty(self) -> NodePath | ManagedNodePath:
        raise NotImplementedError

    @override
    def _create_wall(self) -> NodePath | ManagedNodePath:
        raise NotImplementedError
