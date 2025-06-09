# Copied almost verbatim from another project I work on. Otherwise I would rewrite it basically the same way.

import weakref
from collections.abc import Callable, Iterable
from typing import Any, ClassVar, TypeVar, final, override

from direct.gui.DirectGuiBase import DirectGuiWidget
from observables.observable_generic import ObservableObject
from observables.observable_object import ComputedProperty
from observables.typed_wrappers import DictLikeWrapper
from panda3d.core import NodePath

from cellcrawler.lib.p3d_utils import cleanup_node

T_co = TypeVar("T_co", covariant=True, bound=DirectGuiWidget)
U = TypeVar("U", bound=NodePath)


@final
class DirectGuiWrapper(DictLikeWrapper[T_co]):
    """
    DirectGuiWrapper is a wrapper that allows dict-like access to a DirectGuiWidget.
    The wrapper can automatically react to the edits of observable values used as its parameters.
    Once the GUI object is destroyed, all observable hooks created by the wrapper will be cleaned up.
    """

    count: ClassVar[int] = 0

    @final
    class HookManager:
        def __init__(self, node: str, ref: weakref.ref["DirectGuiWrapper[T_co]"]):
            self.ref = ref
            self.node = node

        def destroy(self):
            if wrapper := self.ref():
                wrapper.destroyTokens()

            DirectGuiWidget.guiDict.pop(self.node, None)

    @override
    def destroyTokens(self) -> None:
        for c in self.children:
            c.destroyTokens()
        self.children = []
        return super().destroyTokens()

    def __init__(self, constructor: type[T_co], /, *args: object, **kwargs: object):
        super().__init__(constructor, *args, **kwargs)
        node_name = f"HookDeleter-{DirectGuiWrapper.count}"
        DirectGuiWrapper.count += 1
        self.children: list[DirectGuiWrapper[Any]] = []
        self.__hookDeleter = NodePath(node_name)
        self.__hookDeleter.reparentTo(self.value)
        self.__hookDeleter.hide()
        self.__hookManager = DirectGuiWrapper.HookManager(node_name, weakref.ref(self))
        # We implement the destroy() method that is currently the only requirement for guiDict items
        # Duck typing my beloved
        DirectGuiWidget.guiDict[node_name] = self.__hookManager  # type: ignore # pyright: ignore[reportArgumentType]


class NodePathComputed(ComputedProperty[U | None]):
    """A wrapper around computed properties that deletes outdated nodepaths from the scene graph."""

    def __init__(self, callback: Callable[[], U | None], dependencies: Iterable[ObservableObject[Any]] | None = None):
        super().__init__(callback, dependencies)
        self.observe_old(self.delete_node)

    def delete_node(self, value: NodePath | None):
        if value is not None:
            cleanup_node(value)
