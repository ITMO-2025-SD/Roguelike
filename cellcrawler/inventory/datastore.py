import abc
from collections.abc import Iterable
from enum import IntEnum
from typing import final
from uuid import UUID, uuid4

from observables.observable_object import ObservableList
from panda3d.core import NodePath

from cellcrawler.core.roguelike_calc_tree import GameNode, PlayerNode

INVENTORY_SIZE = 4 * 4


class ItemCategory(IntEnum):
    ARMOR = 0
    AMULET = 1


class InventoryItem(abc.ABC):
    uuid: UUID
    category: ItemCategory

    def __init__(self, category: ItemCategory) -> None:
        self.category = category
        self.uuid = uuid4()
        self.current_equipment: GameNode[PlayerNode] | None = None

    @abc.abstractmethod
    def make_geom(self) -> NodePath:
        pass

    @abc.abstractmethod
    def make_equipment(self, parent: PlayerNode) -> GameNode[PlayerNode]:
        pass


@final
class Inventory:
    def __init__(self, node: PlayerNode, items: Iterable[InventoryItem]) -> None:
        items = list(items)
        self.equipped: ObservableList[InventoryItem | None] = ObservableList([None for _ in range(len(ItemCategory))])
        self.items = ObservableList(items or [])
        self.calc_node = node

    def add(self, item: InventoryItem) -> bool:
        total_items = len(self.items.value) + sum(x is not None for x in self.equipped.value)
        used_categories = {x.category for x in self.items.value} | {y.category for y in self.equipped.value if y}
        unused_categories = len(ItemCategory) - len(used_categories)
        if (
            # If this clause is false, we will not be able to switch items without throwing them away
            total_items + 1 + unused_categories >= INVENTORY_SIZE + len(ItemCategory)
            # If this clause is false, there's no space.
            or len(self.items.value) >= INVENTORY_SIZE
        ):
            return False
        self.items.value.append(item)
        return True

    def equip(self, uuid: UUID):
        for i, it in enumerate(self.items.value):
            if it.uuid == uuid:
                break
        else:
            raise ValueError(f"No item with ID: {uuid}")

        category = it.category
        if self.equipped.value[category] is not None:
            return

        del self.items.value[i]
        self.equipped.value[it.category] = it
        it.current_equipment = it.make_equipment(self.calc_node)

    def unequip(self, uuid: UUID):
        for i, it in enumerate(self.equipped.value):
            if it and it.uuid == uuid:
                break
        else:
            raise ValueError(f"No item with ID: {uuid}")

        self.items.value.append(it)
        self.equipped.value[i] = None
        if it.current_equipment is not None:
            it.current_equipment.destroy()
            it.current_equipment = None
