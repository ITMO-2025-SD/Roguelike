import abc
from collections.abc import Callable
from typing import Self

from cellcrawler.lib.managed_node import ManagedNode


class PathfindingService(abc.ABC):
    @abc.abstractmethod
    def register(self, node: ManagedNode, callback: Callable[[Self], None]) -> None: ...

    @abc.abstractmethod
    def get_distance(self, x: int, y: int) -> int | None: ...

    @abc.abstractmethod
    def get_distances_to_adjacent(self, x: int, y: int) -> list[tuple[int, tuple[int, int]]]: ...
