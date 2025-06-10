# Copied almost verbatim from another project I work on. Otherwise I would rewrite it basically the same way.

from collections import defaultdict
from collections.abc import Callable
from typing import Any, ClassVar, Generic, Self, TypeVarTuple, cast, final, override

from typing_extensions import TypeVar

# The type of a context.
T = TypeVar("T")
# The type of an event. Events can have multiple parameters.
E = TypeVarTuple("E")

# Type of the parent node
# It is covariant because it only exists in the property.
P_co = TypeVar("P_co", bound="Node[Any, Any]", covariant=True)
# Type of the tree root. All nodes in the tree should have the same root type, so it is invariant.
R = TypeVar("R", bound="RootNode[Any]")
S = TypeVar("S", bound="RootNode[Any]")
# Type of the context data. It is also the same for the entire root.
C = TypeVar("C")

NodeIdT = int
MathPriority = int
TriggerPriority = int

# Internal type to be stored in the ListenerController.
NodeDictEvent = dict[TriggerPriority, dict["Node[Any, R]", Callable[[*E], None]]]
NodeDictMath = dict[MathPriority, dict["Node[Any, R]", Callable[[T, C], T]]]


class Trigger(Generic[*E]):
    """
    Trigger represents a state change that happened. No one can change it anymore, it already happened,
    but any node in the tree can react to the change.

    This is deliberately a class with a generic parameter that is left unused.
    Instances of this class should be created as `Trigger[int, bool]()` etc.
    This is used to make sure that different triggers have correct typechecking of their functions.
    """

    def __init__(self, name: str, debug: bool = False):
        self.name: str = name
        self.debug: bool = debug

    def is_valid(self, *_params: *E) -> bool:
        return True


AnyTrigger = Trigger[*tuple[Any, ...]]


class MathTarget(Generic[T, C]):
    """
    MathTarget represents a state change that is about to happen. Anyone can change it, but no one should assume
    it WILL actually change (also called "The Stateless Principle"). This means that the code accepting MathTargets
    should be a pure function and must not mutate the state in any way.

    This is deliberately a class with a generic parameter that is left unused.
    Instances of this class should be created as `MathTarget[int, Context]()` etc.
    This is used to make sure that different triggers have correct typechecking of their functions.
    """

    def __init__(self, name: str, debug: bool = False):
        self.name: str = name
        self.debug: bool = debug


NodeDestroyed = Trigger[NodeIdT]("NodeDestroyed")
"""Fired right before an object in the tree is destroyed."""


class Node(Generic[P_co, R]):
    _parent: P_co
    root: R
    _children: dict[NodeIdT, "Node[Self, R]"]
    _name: NodeIdT
    max_allocated: ClassVar[NodeIdT] = 0

    @staticmethod
    def allocate() -> NodeIdT:
        Node.max_allocated += 1
        return Node.max_allocated

    def __init__(self, parent: P_co):
        self._parent = parent
        self.root = parent.root
        self._children = {}
        self._name = Node.allocate()
        parent.add_child(self._name, self)

    def add_child(self, name: NodeIdT, child: "Node[Self, R]"):
        self._children[name] = child

    def destroy(self):
        self.dispatch(NodeDestroyed, self._name)
        self.root.listener.remove(self)
        for child in list(self._children.values()):
            child.destroy()
        self._children.clear()
        self._parent._remove_child(self._name)
        del self._parent

    def _remove_child(self, name: NodeIdT):
        self._children.pop(name)

    @property
    def parent(self) -> "P_co":
        return self._parent

    @property
    def name(self):
        return self._name

    def accept(self, event: Trigger[*E], func: Callable[[*E], None], priority: TriggerPriority = 0):
        self.root.listener.add_trigger(self, event, func, priority)

    def add_math_target(self, event: MathTarget[T, C], func: Callable[[T, C], T], priority: MathPriority = 0):
        self.root.listener.add_math_target(self, event, func, priority)

    def dispatch(self, event: Trigger[*E], *data: *E):
        self.root.listener.run_trigger(event, *data)

    def calculate(self, event: MathTarget[T, C], init_value: T, context: C):
        return self.root.listener.run_math(event, init_value, context)


@final
class ParentRemovalBinder(Node[P_co, R]):
    def __init__(self, parent: P_co, oid: NodeIdT):
        super().__init__(parent)
        self.uuid = oid
        self.accept(NodeDestroyed, self.check_destroyed)

    def check_destroyed(self, oid: NodeIdT):
        if oid == self.uuid:
            self.parent.destroy()


class ListenerController(Generic[R]):
    def __init__(self):
        self._node_triggers: dict[Node[Any, R], set[tuple[AnyTrigger, TriggerPriority]]] = defaultdict(set)
        self._node_maths: dict[Node[Any, R], set[tuple[MathTarget[Any, Any], MathPriority]]] = defaultdict(set)
        self._triggers: dict[Trigger[*tuple[Any, ...]], NodeDictEvent[R, *tuple[Any, ...]]] = defaultdict(dict)
        self._mathtargets: dict[MathTarget[Any, Any], NodeDictMath[R, Any, Any]] = defaultdict(dict)

    def remove(self, node: Node[Any, R]):
        triggers = self._node_triggers.pop(node, set())
        for t, p in triggers:
            self._triggers[t][p].pop(node)
        maths = self._node_maths.pop(node, set())
        for t, p in maths:
            self._mathtargets[t][p].pop(node)

    def remove_all(self):
        self._node_triggers.clear()
        self._node_maths.clear()
        self._triggers.clear()
        self._mathtargets.clear()

    def add_trigger(
        self, node: Node[Any, R], event: Trigger[*E], callback: Callable[[*E], None], priority: TriggerPriority
    ):
        self._node_triggers[node].add((event, priority))
        if priority not in self._triggers[event]:
            self._triggers[event][priority] = {}
            self._triggers[event] = dict(sorted(self._triggers[event].items()))
        # pyright doesn't like the variance of Any
        self._triggers[event][priority][node] = callback  # pyright: ignore[reportArgumentType]

    def add_math_target(
        self, node: Node[Any, R], event: MathTarget[T, C], callback: Callable[[T, C], T], priority: MathPriority
    ):
        self._node_maths[node].add((event, priority))
        if priority not in self._mathtargets[event]:
            self._mathtargets[event][priority] = {}
            self._mathtargets[event] = dict(sorted(self._mathtargets[event].items()))
        self._mathtargets[event][priority][node] = callback

    def run_trigger(self, event: Trigger[*E], *context: *E):
        if event.debug:
            print(f"Dispatching event {event.name} with data: {context} to receivers: {self._triggers[event]}")  # noqa: T201
        for prior_dict in self._triggers[event].values():
            for k, t in list(prior_dict.items()):
                if k in prior_dict:
                    t(*context)
                elif event.debug:
                    print(f"Dispatching to node: {k} skipped as the node no longer accepts this trigger")  # noqa: T201
                if not event.is_valid(*context):
                    break

    def run_math(self, event: MathTarget[T, C], init_value: T, context: C) -> T:
        if event.debug:
            print(f"Dispatching math target {event.name} with data: {context} to receivers: {self._mathtargets[event]}")  # noqa: T201
        for prior_dict in self._mathtargets[event].values():
            for t in prior_dict.values():
                init_value = t(init_value, context)
        return init_value


class RootNode(Node[S, S], Generic[S]):
    def __init__(self):  # pyright: ignore[reportMissingSuperCall]
        # Deliberately not calling super's __init__ because all it does is attaching to the parent
        # We don't want that!
        self.root: S = cast(S, self)
        self._children: dict[NodeIdT, Node[Node[S, S], S]] = {}
        self.__listener = ListenerController[S]()

    @override
    def destroy(self):
        self.dispatch(NodeDestroyed, -1)
        self.listener.remove_all()
        self._children.clear()

    @property
    def listener(self):
        return self.__listener
