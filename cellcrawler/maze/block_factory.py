import abc

from panda3d.core import NodePath

from cellcrawler.lib.managed_node import ManagedNodePath
from cellcrawler.maze.maze_data import MazeCell


class BlockFactory(abc.ABC):
    """
    A factory for maze nodes. Should create nodes with the size 1x1x(height). They will be automatically rescaled.
    """

    @abc.abstractmethod
    def _create_empty(self) -> NodePath | ManagedNodePath:
        pass

    @abc.abstractmethod
    def _create_wall(self) -> NodePath | ManagedNodePath:
        pass

    def create(self, typ: MazeCell, scale: float):
        match typ:
            case MazeCell.OPEN:
                node = self._create_empty()
            case MazeCell.WALL:
                node = self._create_wall()

        if isinstance(node, ManagedNodePath):
            # NodeManager already knows about us, no need to retain the wrapper
            node = node.node
        node.set_scale(scale)
        return node
