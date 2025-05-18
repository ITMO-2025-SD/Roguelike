__all__ = ["ManagedNode", "ManagedNodePath"]

import abc
from typing import final, override

from panda3d.core import NodePath


class ManagedNode(abc.ABC):
    def __init__(self, parent: "ManagedNode | None") -> None:
        super().__init__()
        self.parent: ManagedNode | None = parent
        node_manager.add(self)

    def destroy(self):
        node_manager.remove(self)
        self._cleanup()

    @abc.abstractmethod
    def _cleanup(self) -> None:
        pass


class ManagedNodePath(ManagedNode, abc.ABC):
    @abc.abstractmethod
    def _load(self) -> NodePath:
        pass

    def __init__(self, parent: "ManagedNode | None") -> None:
        super().__init__(parent)
        self.node: NodePath = self._load()

    @override
    def _cleanup(self):
        self.node.remove_node()
        del self.node


@final
class NodeManager:
    def __init__(self) -> None:
        self.hierarchy: dict[ManagedNode, list[ManagedNode]] = {}

    def add(self, node: ManagedNode):
        self.hierarchy[node] = []
        if node.parent is not None:
            self.hierarchy[node.parent].append(node)

    def remove(self, node: ManagedNode):
        if node not in self.hierarchy:
            raise RuntimeError(f"Node {node} removed twice")
        children = self.hierarchy.pop(node)
        for c in children:
            c.destroy()


# Singleton :(
node_manager = NodeManager()
