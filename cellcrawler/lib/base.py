import dataclasses
import inspect
from collections.abc import Callable
from typing import Any, ClassVar, Concatenate, Literal, Never, final, overload

from direct.showbase.Loader import Loader
from direct.showbase.ShowBase import ShowBase
from direct.stdpy import file
from direct.task.Task import TaskManager
from panda3d.core import Camera, CollisionTraverser, NodePath, VirtualFileSystem, load_prc_file_data, MouseWatcher, WindowProperties
from rich.traceback import install

from cellcrawler.maze.block_factory import BlockFactory
from cellcrawler.maze.maze_data import MazeData


@final
class CrawlerBase(ShowBase):
    def __init__(self):
        super().__init__()
        self.disable_mouse()

        install(show_locals=True)

        load_prc_file_data("", "model-path /models/built")

        vfs = VirtualFileSystem.get_global_ptr()
        vfs.unmount_all()
        vfs.mount("resources", "/", 0)
        self.cTrav = CollisionTraverser()
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


@dataclasses.dataclass
class RootNodes:
    render: NodePath
    hidden: NodePath
    # NodePath is not generic within P3D code, only in typechecker code, so this must be quoted
    camera: "NodePath[Camera]"
    # Various corner nodes
    top_left: NodePath
    bottom_left: NodePath
    top_right: NodePath
    bottom_right: NodePath


# Another singleton :(
@final
class DependencyInjector:
    bound_types: ClassVar[dict[type[Any], Any]] = {}
    valid_types = {Loader, FileLoader, RootNodes, MazeData, BlockFactory, TaskManager, CollisionTraverser, ShowBase, MouseWatcher, WindowProperties}

    def __init__(self) -> Never:
        raise ValueError("Don't create DependencyInjector")

    @classmethod
    def set_base(cls, base: CrawlerBase):
        cls.bound_types[ShowBase] = base
        cls.bound_types[Loader] = base.loader
        cls.bound_types[FileLoader] = FileLoader(VirtualFileSystem.get_global_ptr())
        cls.bound_types[RootNodes] = RootNodes(
            render=base.render,
            hidden=base.hidden,
            camera=base.cam,
            top_left=base.a2dTopLeft,
            bottom_left=base.a2dBottomLeft,
            top_right=base.a2dTopRight,
            bottom_right=base.a2dBottomRight,
        )
        cls.bound_types[TaskManager] = base.task_mgr
        cls.bound_types[CollisionTraverser] = base.cTrav
        cls.bound_types[MouseWatcher] = base.mouseWatcherNode
        cls.bound_types[WindowProperties] = base.win

    @classmethod
    def set_maze(cls, maze: MazeData):
        cls.bound_types[MazeData] = maze

    @classmethod
    def set_block_factory(cls, factory: BlockFactory):
        cls.bound_types[BlockFactory] = factory

    @classmethod
    def inject[T, R, **P](cls, func: Callable[Concatenate[T, P], R]) -> Callable[[T], R]:
        ann = inspect.get_annotations(func)
        ann.pop("return", None)
        ann.pop("self", None)

        for typ in ann.values():
            if typ not in cls.valid_types:
                raise ValueError(f"Invalid injected type: {typ}")

        def injected(self: T):
            new_kwargs: dict[str, object] = {}
            for key, typ in ann.items():
                if typ not in cls.bound_types:
                    raise ValueError(f"Object does not exist yet: {typ}")

                new_kwargs[key] = cls.bound_types[typ]
            return func(self, **new_kwargs)  # pyright: ignore[reportCallIssue]

        return injected


inject_globals = DependencyInjector.inject
