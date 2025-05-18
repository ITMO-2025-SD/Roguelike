from typing import final, override

from cellcrawler.lib.base import FileLoader, inject_globals
from cellcrawler.maze.level_factory import LevelFactory
from cellcrawler.maze.maze_data import MazeCell, MazeData


@final
class ConstLevelFactory(LevelFactory):
    def __init__(self, path: str) -> None:
        super().__init__()
        self.path = path

    def char_to_mode(self, char: str) -> MazeCell:
        match char:
            case "." | " ":
                return MazeCell.OPEN
            case "#":
                return MazeCell.WALL
            case _:
                raise ValueError(f"Invalid character: {char}")

    @override
    @inject_globals
    def _make_level(self, fl: FileLoader) -> MazeData:
        content = [x.strip() for x in fl(self.path).split("\n")]
        content = [[self.char_to_mode(y) for y in x] for x in content if x]
        return MazeData(content)
