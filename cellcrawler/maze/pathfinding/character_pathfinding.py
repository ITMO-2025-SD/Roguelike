import weakref
from collections import deque
from collections.abc import Callable
from typing import Protocol, Self, final, override

from direct.directnotify.DirectNotifyGlobal import directNotify

from cellcrawler.lib.base import DependencyInjector
from cellcrawler.lib.managed_node import ManagedNode
from cellcrawler.maze.maze_data import MazeData
from cellcrawler.maze.pathfinding.pathfinding import PathfindingService


class SupportsGetCellPos(Protocol):
    def get_cell_pos(self) -> tuple[int, int]: ...
    def run_on_cell_change(self, func: Callable[[Self], None], /) -> None: ...


@final
class CharacterPathfinding(PathfindingService):
    notify = directNotify.newCategory("CharacterPathfinding")

    def __init__(self, player: SupportsGetCellPos):
        self.distances: list[list[int | None]] = []
        self.__handlers: dict[ManagedNode, Callable[[Self], None]] = {}
        self.__player = player

    @override
    def run(self):
        self.__player.run_on_cell_change(self.update_distances)
        self.distances = self.__get_distances(self.__player)

    @override
    def register(self, node: ManagedNode, callback: Callable[[Self], None]):
        self.__handlers[node] = callback
        ref = weakref.ref(self)

        def remove_handler(node1: ManagedNode):
            if self1 := ref():
                self1.__handlers.pop(node1)

        node.run_before_destruction(remove_handler)

    def update_distances(self, player: SupportsGetCellPos):
        self.distances = self.__get_distances(player)
        for h in self.__handlers.values():
            h(self)

    @override
    def get_distance(self, x: int, y: int):
        return self.distances[y][x]

    @override
    def get_distances_to_adjacent(self, x: int, y: int):
        maze = DependencyInjector.get(MazeData)
        options = maze.get_adjacent(x, y)
        distances = [(self.get_distance(x1, y1), (x1, y1)) for x1, y1 in options]
        return [(d, p) for d, p in distances if d is not None]

    def __get_distances(self, player: SupportsGetCellPos) -> list[list[int | None]]:
        maze = DependencyInjector.get(MazeData)
        out: list[list[int | None]] = [[None for _ in row] for row in maze.cells]
        x, y = player.get_cell_pos()
        if x < 0 or y < 0 or x >= maze.width or y >= maze.height:
            self.notify.warning(f"Player is not inside the maze: size {maze.width}x{maze.height} position ({x},{y})!")
            return out
        queue = deque([(x, y, 0)])
        while queue:
            x, y, dist = queue.popleft()
            if out[y][x] is not None:
                continue
            out[y][x] = dist
            for x1, y1 in maze.get_adjacent(x, y):
                queue.append((x1, y1, dist + 1))
        return out
