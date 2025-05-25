import abc
from typing import Final, override

from direct.task.Task import Task, TaskManager
from panda3d.core import CollisionNode

from cellcrawler.character.character_command import CharacterCommand, CommandType
from cellcrawler.lib.base import inject_globals
from cellcrawler.lib.managed_node import ManagedNode, ManagedNodePath


class Character(ManagedNodePath, abc.ABC):
    def __init__(self, parent: ManagedNode | None) -> None:
        self.collision_node: Final = CollisionNode(f"char-{id(self)}")
        super().__init__(parent)

        self.__commands: dict[CommandType, CharacterCommand] = {}
        self.__start_task()

    def set_command(self, key: CommandType, command: CharacterCommand | None):
        if command is None:
            self.__commands.pop(key, None)
        else:
            self.__commands[key] = command

    @inject_globals
    def __start_task(self, task_manager: TaskManager):
        self.__command_task = task_manager.add(self.__exec_command, f"move-{id(self)}")

    def __exec_command(self, task: Task):
        for command in self.__commands.values():
            command.run(self.node, task.dt)
        return task.cont

    @override
    def destroy(self):
        self.__command_task.remove()
        return super().destroy()
