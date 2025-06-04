from direct.actor.Actor import Actor
from direct.gui.DirectGuiBase import DirectGuiWidget
from direct.showbase.DirectObject import DirectObject
from panda3d.core import NodePath


def cleanup_node(node: NodePath):
    if isinstance(node, Actor):
        node.cleanup()
    elif isinstance(node, DirectGuiWidget):
        node.destroy()
    else:
        node.remove_node()

    if isinstance(node, DirectObject):
        node.ignore_all()


def toggle_vis(node: NodePath):
    if node.is_hidden():
        node.show()
    else:
        node.hide()
