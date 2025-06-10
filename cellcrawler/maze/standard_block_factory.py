from typing import override

from panda3d.core import NodePath

from cellcrawler.lib.managed_node import ManagedNodePath
from cellcrawler.lib.model_repository import models
from cellcrawler.maze.block_factory import BlockFactory


class StandardBlockFactory(BlockFactory):
    @override
    def _create_empty(self) -> NodePath | ManagedNodePath | None:
        return None

    @override
    def _create_wall(self) -> NodePath | ManagedNodePath | None:
        return models.load_model("world/wall")
