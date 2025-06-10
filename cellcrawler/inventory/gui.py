import functools
from collections.abc import Callable
from typing import final, override
from uuid import UUID

from direct.gui.DirectButton import DirectButton
from direct.gui.DirectFrame import DirectFrame
from direct.gui.DirectLabel import DirectLabel
from direct.showbase.Loader import Loader
from observables.observable_object import ObservableList
from panda3d.core import NodePath, Vec2

from cellcrawler.inventory.datastore import Inventory, InventoryItem
from cellcrawler.lib.base import inject_globals
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
        *,
        remove_callback: Callable[[UUID], None] | None = None,
    ) -> None:
        self.items = items
        self.callback = callback
        self.node = DirectFrame(frame)
        self.buttons: list[DirectGuiWrapper[DirectButton]] = []
        for i, (x, y) in enumerate(positions):
            btn = self.make_button(i, remove_callback)
            btn.value.set_pos((x, 0, y))
            self.buttons.append(btn)

    @inject_globals
    def __get_trash_can(self, loader: Loader):
        model = loader.load_model("gui/elements.bam", okMissing=False)
        return model.find("**/trash_can")

    @inject_globals
    def __get_inventory_square(self, loader: Loader):
        model = loader.load_model("gui/elements.bam", okMissing=False)
        return model.find("**/inventory_square")

    def make_button(self, idx: int, remove_callback: Callable[[UUID], None] | None) -> DirectGuiWrapper[DirectButton]:
        nodepath = NodePathComputed(functools.partial(self.get_node_at, idx))
        btn = DirectGuiWrapper(
            DirectButton,
            parent=self.node,
            relief=None,
            geom=self.__get_inventory_square(),
            frameSize=(-BUTTON_SIZE / 2, BUTTON_SIZE / 2, -BUTTON_SIZE / 2, BUTTON_SIZE / 2),
            geom_scale=BUTTON_SIZE * 2,
            command=lambda: self.run_callback_at(idx, self.callback),
        )
        item = DirectGuiWrapper(DirectFrame, parent=btn.value, image=nodepath, image_scale=BUTTON_SIZE, relief=None)
        btn.children.append(item)
        if remove_callback is not None:
            trash = DirectGuiWrapper(
                DirectButton,
                btn.value,
                geom=self.__get_trash_can(),
                command=lambda: self.run_callback_at(idx, remove_callback),
                relief=None,
                scale=0.3,
                pos=(0.06, 0, 0.06),
            )

            def hide_button(np: NodePath | None):
                if not np or np.name == "aaa":
                    trash.value.hide()
                else:
                    trash.value.show()

            hide_button(nodepath.value)
            nodepath.observe(hide_button)
            btn.children.append(trash)
        return btn

    def get_node_at(self, idx: int) -> NodePath:
        if idx >= len(self.items.value):
            return NodePath("aaa")
        item = self.items.value[idx]
        if item is None:
            return NodePath("aaa")
        return item.make_geom()

    def run_callback_at(self, idx: int, callback: Callable[[UUID], None]) -> None:
        if idx >= len(self.items.value):
            return None
        item = self.items.value[idx]
        if item is None:
            return None
        return callback(item.uuid)


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
        self.unequipped = ItemFrame(self.frame, inv.items, inv.equip, unequipped_positions, remove_callback=inv.remove)

    @override
    def _load(self) -> DirectFrame:
        return self.frame
