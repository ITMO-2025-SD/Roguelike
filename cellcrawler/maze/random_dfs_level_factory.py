from typing import final, override

from cellcrawler.lib.base import FileLoader, inject_globals
from cellcrawler.maze.level_factory import LevelFactory
from cellcrawler.maze.maze_data import MazeCell, MazeData
from random import randint


@final
class RandomDfsLevelFactory(LevelFactory):
    def __init__(self, seed: int) -> None:
        super().__init__()
        self.seed = seed

    def char_to_mode(self, char: str) -> MazeCell:
        match char:
            case "." | " ":
                return MazeCell.OPEN
            case "#":
                return MazeCell.WALL
            case _:
                raise ValueError(f"Invalid character: {char}")
            
    def dfs(self, cells):
        rows = len(cells)
        cols = len(cells[0])
        st = [(1, 1)] # can be random cell with odd coords
        diffs = [(0, 2),(0, -2),(2, 0),(-2, 0)]

        while st:
            (x, y) = st.pop()
            cells[x][y] = ' '

            candidates = [
                (x + dx, y + dy) 
                for (dx, dy) in diffs 
                if 0 <= x + dx < rows and 0 <= y + dy < cols and cells[x + dx][y + dy] == '#'
            ]

            if candidates:
                st.append((x, y))
                (nx, ny) = candidates[randint(0, len(candidates) - 1)]
                cells[x + (nx - x) // 2][y + (ny - y) // 2] = ' '
                st.append((nx, ny))

        return cells

    # @inject_globals
    @override
    def _make_level(self) -> MazeData:
        # ROWS and COLS must be odd
        rows = 51
        cols = 51
        cells = self.dfs( [['#' for j in range(cols)] for i in range(rows)] )
        cells = [[self.char_to_mode(y) for y in x] for x in cells]
        
        return MazeData(cells)
