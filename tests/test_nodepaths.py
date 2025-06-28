from observables.observable_object import Value
from panda3d.core import NodePath

from cellcrawler.lib.observable_utils import NodePathComputed


def test_observable_nodepath():
    np_parent = NodePath("parent")

    toggle = Value(False)

    @NodePathComputed
    def computed():
        if toggle.value:
            node = NodePath("new")
            node.reparent_to(np_parent)
            return node
        return None

    assert computed.value is None
    assert np_parent.get_num_children() == 0

    toggle.value = True
    assert computed.value is not None
    assert np_parent.get_num_children() == 1

    toggle.value = False
    assert computed.value is None
    assert np_parent.get_num_children() == 0
