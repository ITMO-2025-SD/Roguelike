from random import randint
from typing import final, override

from cellcrawler.maze.level_factory import LevelFactory
from cellcrawler.maze.maze_data import MazeCell, MazeData


@final
class RandomDfsLevelFactory(LevelFactory):
    def __init__(self, size: int) -> None:
        super().__init__()
        # Size must be odd or the DFS does not work, so we make it odd
        self.size = 2 * size + 1

    def dfs(self, cells: list[list[MazeCell]]):
        rows = len(cells)
        cols = len(cells[0])
        st = [(1, 1)]  # can be random cell with odd coords
        diffs = [(0, 2), (0, -2), (2, 0), (-2, 0)]

        while st:
            (x, y) = st.pop()
            cells[x][y] = MazeCell.OPEN

            candidates = [
                (x + dx, y + dy)
                for (dx, dy) in diffs
                if 0 <= x + dx < rows and 0 <= y + dy < cols and cells[x + dx][y + dy] == MazeCell.WALL
            ]

            if candidates:
                st.append((x, y))
                (nx, ny) = candidates[randint(0, len(candidates) - 1)]
                cells[x + (nx - x) // 2][y + (ny - y) // 2] = MazeCell.OPEN
                st.append((nx, ny))

        return cells

    @override
    def _make_level(self) -> MazeData:
        cells = self.dfs([[MazeCell.WALL for _ in range(self.size)] for _ in range(self.size)])

        return MazeData(cells)
