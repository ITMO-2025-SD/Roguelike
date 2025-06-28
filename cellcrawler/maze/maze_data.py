import dataclasses
from collections import Counter
from enum import Enum, auto


class MazeCellBasic(Enum):
    OPEN = auto()
    WALL = auto()


MazeCell = MazeCellBasic


def is_visitable(cell: MazeCell):
    match cell:
        case MazeCellBasic.OPEN:
            return True
        case MazeCellBasic.WALL:
            return False


@dataclasses.dataclass
class MazeData:
    cells: list[list[MazeCell]]
    occupations: dict[tuple[int, int], int] = dataclasses.field(default_factory=Counter[tuple[int, int]])

    def set_occupied(self, pos: tuple[int, int]):
        self.occupations[pos] += 1

    def clear_occupied(self, pos: tuple[int, int]):
        self.occupations[pos] -= 1
        if not self.occupations[pos]:
            del self.occupations[pos]

    def get_adjacent(self, x: int, y: int):
        out: list[tuple[int, int]] = []
        if not (0 <= x < len(self.cells[0])) or not (0 <= y < len(self.cells)):
            return out
        if x > 0 and is_visitable(self.cells[y][x - 1]):
            out.append((x - 1, y))
        if x + 1 < len(self.cells[0]) and is_visitable(self.cells[y][x + 1]):
            out.append((x + 1, y))
        if y > 0 and is_visitable(self.cells[y - 1][x]):
            out.append((x, y - 1))
        if y + 1 < len(self.cells) and is_visitable(self.cells[y + 1][x]):
            out.append((x, y + 1))
        return out

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
