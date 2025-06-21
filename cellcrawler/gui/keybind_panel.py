from typing import final, override

from direct.gui.DirectFrame import DirectFrame
from direct.gui.DirectLabel import DirectLabel
from direct.showbase.DirectObject import DirectObject
from direct.showbase.ShowBase import ShowBase

from cellcrawler.lib.base import RootNodes, inject_globals
from cellcrawler.lib.managed_node import ManagedDirectObject, ManagedGui, ManagedNode


@final
class DebugListener(ManagedDirectObject):
    def __init__(self, parent: "ManagedNode | None") -> None:
        self.collisions_visible = False
        super().__init__(parent)

    @override
    def _load(self) -> DirectObject:
        o = DirectObject()
        o.accept("j", self.toggle_collisions)
        o.accept("o", self.toggle_oobe)
        return o

    @inject_globals
    def toggle_oobe(self, base: ShowBase):
        base.oobe()

    @inject_globals
    def toggle_collisions(self, nodes: RootNodes):
        collisions = nodes.render.find_all_matches("**/+CollisionNode")
        if self.collisions_visible:
            self.collisions_visible = False
            for c in collisions:
                c.hide()
        else:
            self.collisions_visible = True
            for c in collisions:
                c.show()


@final
class KeybindPanel(ManagedGui):
    DEBUG = True

    @inject_globals
    def _load(self, nodes: RootNodes):
        frame = DirectFrame()
        keybinds = [
            ("w", "Move forward"),
            ("s", "Move backward"),
            ("a", "Move left"),
            ("d", "Move right"),
            ("q", "Rotate left"),
            ("r", "Rotate right"),
            ("i", "Open inventory"),
            ("space", "Attack"),
        ]
        if self.DEBUG:
            DebugListener(self)
            keybinds.append(("j", "Debug collisions"))
            keybinds.append(("o", "Oobe Camera"))
        for i, (button, name) in enumerate(keybinds):
            self.add_button(frame, i + 1, button, name)
        frame.reparent_to(nodes.top_right)
        return frame

    def add_button(self, frame: DirectFrame, idx: int, button: str, name: str):
        row = DirectFrame(parent=frame, pos=(0, 0, -idx * 0.1), scale=0.1)
        DirectLabel(parent=row, pos=(-10, 0, 0), text=button, relief=None)
        DirectLabel(parent=row, pos=(-5, 0, 0), text=name, relief=None)
