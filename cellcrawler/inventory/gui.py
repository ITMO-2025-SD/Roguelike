import functools
from collections.abc import Callable
from typing import final, override
from uuid import UUID

from direct.gui import DirectGuiGlobals
from direct.gui.DirectButton import DirectButton
from direct.gui.DirectFrame import DirectFrame
from direct.gui.DirectLabel import DirectLabel
from observables.observable_object import ObservableList
from panda3d.core import NodePath, Vec2

from cellcrawler.inventory.datastore import Inventory, InventoryItem
from cellcrawler.lib.managed_node import ManagedGui, ManagedNode
from cellcrawler.lib.observable_utils import DirectGuiWrapper, NodePathComputed

BUTTON_SIZE = 0.2
BUTTON_DISTANCE = 0.225  # includes padding


@final
class ItemFrame:
    def __init__(
        self,
        frame: DirectFrame,
        items: ObservableList[InventoryItem] | ObservableList[InventoryItem | None],
        callback: Callable[[UUID], None],
        positions: list[Vec2],
    ) -> None:
        self.items = items
        self.callback = callback
        self.node = DirectFrame(frame)
        self.buttons: list[DirectGuiWrapper[DirectButton]] = []
        for i, (x, y) in enumerate(positions):
            btn = self.make_button(i)
            btn.value.set_pos((x, 0, y))
            self.buttons.append(btn)

    def make_button(self, idx: int) -> DirectGuiWrapper[DirectButton]:
        return DirectGuiWrapper(
            DirectButton,
            parent=self.node,
            image=NodePathComputed(functools.partial(self.get_node_at, idx)),
            relief=DirectGuiGlobals.SUNKEN,
            frameSize=(-BUTTON_SIZE / 2, BUTTON_SIZE / 2, -BUTTON_SIZE / 2, BUTTON_SIZE / 2),
            image_scale=BUTTON_SIZE,
            image_pos=(0, 0, -BUTTON_SIZE / 2),  # wtf?
            command=lambda: self.run_callback_at(idx),
        )

    def get_node_at(self, idx: int) -> NodePath:
        if idx >= len(self.items.value):
            return NodePath("a")
        item = self.items.value[idx]
        if item is None:
            return NodePath("a")
        return item.make_geom()

    def run_callback_at(self, idx: int) -> None:
        if idx >= len(self.items.value):
            return None
        item = self.items.value[idx]
        if item is None:
            return None
        return self.callback(item.uuid)


@final
class InventoryGUI(ManagedGui):
    def __init__(self, parent: ManagedNode | None, inv: Inventory) -> None:
        self.frame = DirectFrame()
        super().__init__(parent)
        self.equipped_label = DirectLabel(
            relief=None, pos=(-0.5, 0, 0.8), text="Equipped", parent=self.frame, scale=0.1
        )
        self.inventory_label = DirectLabel(
            relief=None, pos=(0.5, 0, 0.8), text="Inventory", parent=self.frame, scale=0.1
        )

        equipped_positions = [
            Vec2(-0.5, BUTTON_DISTANCE / 2),  # armor
            Vec2(-0.5, -BUTTON_DISTANCE / 2),  # amulet
        ]
        unequipped_positions: list[Vec2] = []
        for i in range(4):
            for j in range(4):
                unequipped_positions.append(Vec2(0.1 + BUTTON_DISTANCE * j, BUTTON_DISTANCE * (1.5 - i)))
        self.equipped = ItemFrame(self.frame, inv.equipped, inv.unequip, equipped_positions)
        self.unequipped = ItemFrame(self.frame, inv.items, inv.equip, unequipped_positions)

    @override
    def _load(self) -> DirectFrame:
        return self.frame
