from typing import ClassVar, override

from cellcrawler.core.roguelike_calc_tree import GameNode, LevelTree, MobDied
from cellcrawler.lib.calculation_tree import MathTarget
from cellcrawler.lib.managed_node import ManagedNode


def test_calctree():
    level_tree = LevelTree()
    node = GameNode(level_tree)
    tree2 = LevelTree()

    arr: list[int] = []
    node.accept(MobDied, lambda: arr.append(0))
    level_tree.dispatch(MobDied)
    assert arr == [0]
    # Events only get dispatched inside the correct tree
    tree2.dispatch(MobDied)
    assert arr == [0]
    # Accept is permanent
    level_tree.dispatch(MobDied)
    assert arr == [0, 0]

    math_test = MathTarget[int, None]("MathTest")
    node.add_math_target(math_test, lambda v, u: v * 2)
    assert level_tree.calculate(math_test, 10, None) == 20
    assert tree2.calculate(math_test, 10, None) == 10


def test_managed_nodes():
    class ManagedCounter(ManagedNode):
        counter: ClassVar[int] = 0

        def __init__(self, parent: "ManagedNode | None") -> None:
            super().__init__(parent)
            ManagedCounter.counter += 1

        @override
        def _cleanup(self) -> None:
            ManagedCounter.counter -= 1

    root = ManagedCounter(None)
    assert ManagedCounter.counter == 1
    child = ManagedCounter(root)
    _grandchild = ManagedCounter(child)
    assert ManagedCounter.counter == 3
    unrelated = ManagedCounter(None)
    assert ManagedCounter.counter == 4
    root.destroy()
    assert ManagedCounter.counter == 1
    unrelated.destroy()
    assert ManagedCounter.counter == 0
