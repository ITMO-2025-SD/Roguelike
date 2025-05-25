import abc
from typing import override

from direct.actor.Actor import Actor
from direct.gui.DirectGuiBase import DirectGuiWidget
from direct.showbase.DirectObject import DirectObject
from panda3d.core import NodePath


class ManagedNode(abc.ABC):
    def __init__(self, parent: "ManagedNode | None") -> None:
        super().__init__()
        self.parent: ManagedNode | None = parent
        self.children: set[ManagedNode] = set()
        self.__removed = False
        if parent is not None:
            parent.children.add(self)

    def destroy(self):
        if self.__removed:
            raise RuntimeError(f"Node {self} removed twice")
        self.__removed = True
        for c in self.children:
            c.destroy()
        self.children = set()
        self._cleanup()
        if self.parent:
            self.parent.children.discard(self)

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


class ManagedActor(ManagedNode, abc.ABC):
    @abc.abstractmethod
    def _load(self) -> Actor:
        pass

    def __init__(self, parent: "ManagedNode | None") -> None:
        super().__init__(parent)
        self.node: Actor = self._load()

    @override
    def _cleanup(self):
        self.node.cleanup()
        del self.node


class ManagedGui(ManagedNode, abc.ABC):
    @abc.abstractmethod
    def _load(self) -> DirectGuiWidget:
        pass

    def __init__(self, parent: "ManagedNode | None") -> None:
        super().__init__(parent)
        self.node: DirectGuiWidget = self._load()

    @override
    def _cleanup(self):
        self.node.destroy()
        del self.node


class ManagedDirectObject(ManagedNode, abc.ABC):
    @abc.abstractmethod
    def _load(self) -> DirectObject:
        pass

    def __init__(self, parent: "ManagedNode | None") -> None:
        super().__init__(parent)
        self.node: DirectObject = self._load()

    @override
    def _cleanup(self):
        self.node.ignore_all()
        del self.node
