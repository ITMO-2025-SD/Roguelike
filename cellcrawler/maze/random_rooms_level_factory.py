from random import choice, randint
from typing import final, override

from cellcrawler.maze.level_factory import LevelFactory
from cellcrawler.maze.maze_data import MazeCell, MazeData

type RoomT = tuple[tuple[int, int], tuple[int, int]]


@final
class RandomRoomsLevelFactory(LevelFactory):
    def __init__(self, size: int, room_min_size: int, room_max_size: int, attempts: int) -> None:
        super().__init__()
        # Size must be odd or the DFS does not work, so we make it odd
        self.full_size = 2 * size + 1
        self.avalible_size = size
        self.room_min_size = room_min_size
        self.room_max_size = room_max_size
        self.attempts = attempts

        self.color_map = [[-1 for _ in range(self.full_size)] for _ in range(self.full_size)]
        self.rooms: list[RoomT] = []
        self.components = 0

    def gen_room_coordinates(self):
        x0 = randint(0, self.avalible_size - self.room_min_size)
        y0 = randint(0, self.avalible_size - self.room_min_size)
        x1 = x0 + self.room_min_size + randint(0, self.room_max_size - self.room_min_size) - 1
        y1 = y0 + self.room_min_size + randint(0, self.room_max_size - self.room_min_size) - 1
        # propably will need to change room representation
        return ((2 * x0 + 1, 2 * y0 + 1), (2 * x1 + 1, 2 * y1 + 1))

    def check_for_open_space(self, room: RoomT, cells: list[list[MazeCell]]) -> bool:
        ((x0, y0), (x1, y1)) = room

        for i in range(x0, x1 + 1):
            for j in range(y0, y1 + 1):
                if cells[i][j] == MazeCell.OPEN:
                    return True

        return False

    # Very rarely there could be cases when no room is generated like 1 in billion
    def generate_rooms(self, cells: list[list[MazeCell]]) -> list[list[MazeCell]]:
        for _ in range(self.attempts):
            room = self.gen_room_coordinates()
            ((x0, y0), (x1, y1)) = room
            if x1 >= self.full_size or y1 >= self.full_size:
                continue

            if self.check_for_open_space(room, cells):
                continue

            # we may need this later
            self.rooms.append(room)

            # O(n^2) check of overlapping probably can be done better, but for now ok
            for i in range(x0, x1 + 1):
                for j in range(y0, y1 + 1):
                    cells[i][j] = MazeCell.OPEN
                    self.color_map[i][j] = self.components

            self.components = self.components + 1

        return cells

    # (st_x, st_y) can be random cell with odd coords
    def dfs(self, cells: list[list[MazeCell]], st_x: int, st_y: int) -> list[list[MazeCell]]:
        rows = len(cells)
        cols = len(cells[0])
        st = [(st_x, st_y)]
        diffs = [(0, 2), (0, -2), (2, 0), (-2, 0)]

        while st:
            (x, y) = st.pop()
            cells[x][y] = MazeCell.OPEN
            self.color_map[x][y] = self.components

            candidates = [
                (x + dx, y + dy)
                for (dx, dy) in diffs
                if 0 <= x + dx < rows and 0 <= y + dy < cols and cells[x + dx][y + dy] == MazeCell.WALL
            ]

            if candidates:
                st.append((x, y))
                (nx, ny) = candidates[randint(0, len(candidates) - 1)]
                cells[x + (nx - x) // 2][y + (ny - y) // 2] = MazeCell.OPEN
                self.color_map[x + (nx - x) // 2][y + (ny - y) // 2] = self.components
                st.append((nx, ny))

        self.components = self.components + 1

        return cells

    def gen_maze_components(self, cells: list[list[MazeCell]]) -> list[list[MazeCell]]:
        for i in range(1, self.full_size, 2):
            for j in range(1, self.full_size, 2):
                if self.color_map[i][j] < 0:
                    cells = self.dfs(cells, i, j)

        return cells

    def get_component_graph(self) -> list[dict[int, list[tuple[int, int]]]]:
        diffs = [(0, 2), (0, -2), (2, 0), (-2, 0)]
        rows = self.full_size
        cols = self.full_size

        component_graph: list[dict[int, list[tuple[int, int]]]] = [{} for _ in range(self.components)]
        for x in range(1, self.full_size - 1):
            for y in range(1, self.full_size - 1):
                cp = self.color_map[x][y]
                if cp >= 0:
                    for dx, dy in diffs:
                        if (
                            0 <= x + dx < rows
                            and 0 <= y + dy < cols
                            and self.color_map[x + dx][y + dy] >= 0
                            and cp != self.color_map[x + dx][y + dy]
                        ):
                            cn = self.color_map[x + dx][y + dy]
                            if cn not in component_graph[cp]:
                                component_graph[cp][cn] = []
                            component_graph[cp][cn].append((x + dx // 2, y + dy // 2))

        return component_graph

    def connect_components(self, cells: list[list[MazeCell]]) -> list[list[MazeCell]]:
        primary_room = randint(0, len(self.rooms) - 1)
        component_graph = self.get_component_graph()

        visited = [False for _ in range(self.components)]
        st = [primary_room]

        while st:
            cur = st.pop()
            visited[cur] = True

            # May add opening some connectors on random
            for component, lst in component_graph[cur].items():
                if not visited[component]:
                    (x, y) = choice(lst)
                    # Also here may place doors instead
                    cells[x][y] = MazeCell.OPEN
                    visited[component] = True
                    st.append(component)

        return cells

    # 1 <= cell_x, cell_y <= self.full_size - 2
    def cell_is_dead_end(self, cells: list[list[MazeCell]], x: int, y: int) -> bool:
        if cells[x][y] == MazeCell.WALL:
            return False

        diffs = [(0, 1), (0, -1), (1, 0), (-1, 0)]

        cnt = 0
        for dx, dy in diffs:
            if cells[x + dx][y + dy] == MazeCell.OPEN:
                cnt = cnt + 1

        return cnt == 1

    def clear_dead_ends(self, cells: list[list[MazeCell]]):
        dead_ends: list[tuple[int, int]] = []
        for x in range(1, self.full_size - 1):
            for y in range(1, self.full_size - 1):
                if self.cell_is_dead_end(cells, x, y):
                    dead_ends.append((x, y))

        diffs = [(0, 1), (0, -1), (1, 0), (-1, 0)]

        while dead_ends:
            (x, y) = dead_ends.pop()
            cells[x][y] = MazeCell.WALL
            self.color_map[x][y] = -1
            for dx, dy in diffs:
                if self.cell_is_dead_end(cells, x + dx, y + dy):
                    dead_ends.append((x + dx, y + dy))

        return cells

    @override
    def _make_level(self) -> MazeData:
        cells = [[MazeCell.WALL for _ in range(self.full_size)] for _ in range(self.full_size)]
        cells = self.generate_rooms(cells)
        cells = self.gen_maze_components(cells)
        cells = self.connect_components(cells)
        cells = self.clear_dead_ends(cells)

        return MazeData(cells)
