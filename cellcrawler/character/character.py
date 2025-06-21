import abc
import math
from collections.abc import Callable
from enum import Enum, auto
from typing import Any, Final, Generic, Self, TypeVar, cast, override

from direct.task.Task import Task, TaskManager
from panda3d.core import BitMask32, ClockObject, CollisionNode, GeomNode, NodePath, Vec4

from cellcrawler.core.roguelike_calc_tree import CharacterNode, LevelTree
from cellcrawler.lib.base import DependencyInjector, inject_globals
from cellcrawler.lib.managed_node import ManagedNode, ManagedNodePath
from cellcrawler.lib.model_repository import models
from cellcrawler.lib.p3d_utils import make_polyset_solids
from cellcrawler.maze.blockpos_utils import maze_to_world_position, world_to_maze_position
from cellcrawler.maze.maze_data import MazeData

CalcNodeT = TypeVar("CalcNodeT", bound=CharacterNode)

BEAM_INACTIVE_COLOR = Vec4(1, 1, 0.7, 1)
BEAM_ACTIVE_COLOR = Vec4(1, 0.2, 0.2, 1)
PUSHER_COLLIDE_MASK = BitMask32(0x0001)
BEAM_COLLIDE_MASK = BitMask32(0x0002)


class CommandType(Enum):
    MOVE = auto()
    ROTATE = auto()
    MOB_MOVEMENT = auto()
    ATTACK = auto()


class Character(ManagedNodePath, Generic[CalcNodeT], abc.ABC):
    def __init__(self, parent: ManagedNode | None) -> None:
        self.collision_node: Final = CollisionNode(f"char-{id(self)}")
        self.collision_node.set_into_collide_mask(PUSHER_COLLIDE_MASK | BEAM_COLLIDE_MASK)
        self.collision_node.set_from_collide_mask(PUSHER_COLLIDE_MASK)
        self.__beam: NodePath | None = None
        self.__beam_collider: Final = CollisionNode(f"beam-{id(self)}")
        self.__beam_collider.set_collide_mask(BEAM_COLLIDE_MASK)
        super().__init__(parent)

        self.calc_node: Final = self.__make_calc_node()
        self.__commands: dict[CommandType, CharacterCommand] = {}
        task_manager = DependencyInjector.get(TaskManager)
        self.__command_task = task_manager.add(self.__exec_command, f"exec-character-commands-{id(self)}")
        self.__on_command_done: list[Callable[[Self, list[CommandType]], None]] = []
        self.__prev_position: tuple[int, int] = (-1, -1)
        self.__on_cell_change: list[Callable[[Self], None]] = []
        characters.add(self)

    def create_attacking_beam(self, height: float, length: float, fov: float) -> NodePath:
        beam = models.load_model("characters/beam")
        tan = math.tan(math.radians(fov / 2))
        beam.set_scale((length * tan, length / math.sqrt(2), height))
        beam.set_color(BEAM_INACTIVE_COLOR)
        self.__beam = beam
        colliders = make_polyset_solids(cast(GeomNode, beam.get_child(0).node()))
        for s in colliders:
            self.__beam_collider.add_solid(s)
        self.__beam.attach_new_node(self.__beam_collider)  # .show()
        return beam

    @property
    def attacking_beam(self):
        return self.__beam

    def move_to(self, maze_pos: tuple[int, int]):
        self.node.set_pos(maze_to_world_position(*maze_pos))

    def run_on_command_done(self, func: Callable[[Self, list[CommandType]], None]):
        self.__on_command_done.append(func)

    def run_on_cell_change(self, func: Callable[[Self], None]):
        self.__on_cell_change.append(func)

    def get_cell_pos(self):
        return world_to_maze_position(self.node.get_pos())

    @inject_globals
    def __make_calc_node(self, level: LevelTree) -> CalcNodeT:
        return self.create_calc_node(level)

    @abc.abstractmethod
    def create_calc_node(self, parent: LevelTree) -> CalcNodeT:
        pass

    def get_command(self, key: CommandType):
        return self.__commands.get(key)

    def set_command(self, key: CommandType, command: "CharacterCommand | None"):
        if command is None:
            self.__commands.pop(key, None)
        else:
            self.__commands[key] = command

    def __update_occupied_position(self):
        new_position = self.get_cell_pos()
        if new_position != self.__prev_position:
            maze = DependencyInjector.get(MazeData)
            if self.__prev_position != (-1, -1):
                maze.clear_occupied(self.__prev_position)
            self.__prev_position = new_position
            maze.set_occupied(new_position)
            for cmd in self.__on_cell_change:
                cmd(self)

    def __exec_command(self, task: Task):
        removed_commands: list[CommandType] = []
        for key, command in self.__commands.items():
            command.run(self, DependencyInjector.get(ClockObject).dt)
            if command.done:
                removed_commands.append(key)
        self.__update_occupied_position()
        for key in removed_commands:
            del self.__commands[key]
        if removed_commands:
            for hook in self.__on_command_done:
                hook(self, removed_commands)
        return task.cont

    @override
    def destroy(self):
        self.__command_task.remove()
        characters.remove(self)
        return super().destroy()


class CharacterCommand(abc.ABC):
    done: bool = False

    def set_done(self):
        self.done = True

    @abc.abstractmethod
    def run(self, character: Character[Any], dt: float) -> None:
        pass


class CharacterRepository:
    def __init__(self) -> None:
        self.__chars: set[Character[Any]] = set()

    def add(self, char: Character[Any]):
        self.__chars.add(char)

    def remove(self, char: Character[Any]):
        self.__chars.discard(char)

    def all(self):
        return list(self.__chars)


characters = CharacterRepository()
