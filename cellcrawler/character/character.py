import abc
from collections.abc import Callable
from typing import Final, Generic, Self, TypeVar, override

from direct.task.Task import Task, TaskManager
from panda3d.core import CollisionNode

from cellcrawler.character.character_command import CharacterCommand, CommandType
from cellcrawler.core.roguelike_calc_tree import CharacterNode, LevelTree
from cellcrawler.lib.base import DependencyInjector, inject_globals
from cellcrawler.lib.managed_node import ManagedNode, ManagedNodePath
from cellcrawler.maze.blockpos_utils import maze_to_world_position, world_to_maze_position
from cellcrawler.maze.maze_data import MazeData

CalcNodeT = TypeVar("CalcNodeT", bound=CharacterNode)


class Character(ManagedNodePath, Generic[CalcNodeT], abc.ABC):
    def __init__(self, parent: ManagedNode | None) -> None:
        self.collision_node: Final = CollisionNode(f"char-{id(self)}")
        super().__init__(parent)

        self.calc_node: Final = self.__make_calc_node()
        self.__commands: dict[CommandType, CharacterCommand] = {}
        task_manager = DependencyInjector.get(TaskManager)
        self.__command_task = task_manager.add(self.__exec_command, f"exec-character-commands-{id(self)}")
        self.__on_command_done: list[Callable[[Self, list[CommandType]], None]] = []
        self.__prev_position: tuple[int, int] = (-1, -1)

    def move_to(self, maze_pos: tuple[int, int]):
        self.node.set_pos(maze_to_world_position(*maze_pos))

    def run_on_command_done(self, func: Callable[[Self, list[CommandType]], None]):
        self.__on_command_done.append(func)

    def get_cell_pos(self):
        return world_to_maze_position(self.node.get_pos())

    @inject_globals
    def __make_calc_node(self, level: LevelTree) -> CalcNodeT:
        return self.create_calc_node(level)

    @abc.abstractmethod
    def create_calc_node(self, parent: LevelTree) -> CalcNodeT:
        pass

    def set_command(self, key: CommandType, command: CharacterCommand | None):
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

    def __exec_command(self, task: Task):
        removed_commands: list[CommandType] = []
        for key, command in self.__commands.items():
            command.run(self.node, self.calc_node, task.dt)
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
        return super().destroy()
