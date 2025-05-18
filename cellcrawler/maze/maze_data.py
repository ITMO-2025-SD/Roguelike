import dataclasses
from enum import Enum, auto


class MazeCellBasic(Enum):
    OPEN = auto()
    WALL = auto()


MazeCell = MazeCellBasic


@dataclasses.dataclass
class MazeData:
    cells: list[list[MazeCell]]

    def __post_init__(self):
        if not self.cells:
            raise ValueError("must have >= 1 row")
        if not self.cells[0]:
            raise ValueError("must have >= 1 column")
        if len({len(x) for x in self.cells}) != 1:
            raise ValueError("uneven cells")

    @property
    def width(self):
        return len(self.cells[0])

    @property
    def height(self):
        return len(self.cells)
