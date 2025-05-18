import inspect
from collections.abc import Callable
from typing import Any, ClassVar, Concatenate, Literal, Never, final, overload

from direct.showbase.Loader import Loader
from direct.showbase.ShowBase import ShowBase
from direct.stdpy import file
from panda3d.core import VirtualFileSystem

from cellcrawler.maze.block_factory import BlockFactory
from cellcrawler.maze.maze_data import MazeData
from cellcrawler.maze.standard_block_factory import StandardBlockFactory


@final
class CrawlerBase(ShowBase):
    def __init__(self):
        super().__init__()

        vfs = VirtualFileSystem.get_global_ptr()
        if not vfs.unmount_all() or not vfs.mount("resources", "/", 0):
            raise RuntimeError("unable to init vfs")

        self.block_factory = StandardBlockFactory()
        DependencyInjector.set_base(self)


@final
class FileLoader:
    def __init__(self, vfs: VirtualFileSystem) -> None:
        self.__vfs = vfs

    @overload
    def __call__(self, path: str, mode: Literal["rt"] = "rt") -> str: ...

    @overload
    def __call__(self, path: str, mode: Literal["rb"]) -> bytes: ...

    def __call__(self, path: str, mode: Literal["rt", "rb"] = "rt") -> str | bytes:
        path_filename = self.__vfs.get_file("/" + path)
        if not path_filename:
            raise ValueError(f"unable to resolve filename {path}")
        with file.open(path_filename, mode) as f:
            return f.read()


# Another singleton :(
@final
class DependencyInjector:
    bound_types: ClassVar[dict[type[Any], Any]] = {}

    def __init__(self) -> Never:
        raise ValueError("Don't create DependencyInjector")

    @classmethod
    def set_base(cls, base: CrawlerBase):
        cls.bound_types[Loader] = base.loader
        cls.bound_types[BlockFactory] = base.block_factory
        cls.bound_types[FileLoader] = FileLoader(VirtualFileSystem.get_global_ptr())

    @classmethod
    def set_maze(cls, maze: MazeData):
        cls.bound_types[MazeData] = maze

    @classmethod
    def inject[T, R, **P](cls, func: Callable[Concatenate[T, P], R]) -> Callable[[T], R]:
        ann = inspect.get_annotations(func)
        ann.pop("return", None)
        ann.pop("self", None)

        def injected(self: T):
            new_kwargs: dict[str, object] = {}
            for key, typ in ann.items():
                if typ not in cls.bound_types:
                    raise ValueError(f"Unknown type: {typ}")

                new_kwargs[key] = cls.bound_types[typ]
            return func(self, **new_kwargs)  # pyright: ignore[reportCallIssue]

        return injected


inject_globals = DependencyInjector.inject
