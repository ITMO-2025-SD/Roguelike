import abc
from typing import override

from direct.task.Task import Task, TaskManager

from cellcrawler.character.movement_command import CharacterCommand
from cellcrawler.lib.base import inject_globals
from cellcrawler.lib.managed_node import ManagedNode, ManagedNodePath


class Character(ManagedNodePath, abc.ABC):
    def __init__(self, parent: ManagedNode | None) -> None:
        super().__init__(parent)

        self.__command: CharacterCommand | None = None
        self.__start_task()

    def set_command(self, command: CharacterCommand | None = None):
        self.__command = command

    @inject_globals
    def __start_task(self, task_manager: TaskManager):
        self.__command_task = task_manager.add(self.__exec_command, f"move-{id(self)}")

    def __exec_command(self, task: Task):
        if self.__command is not None:
            self.__command.run(self.node, task.dt)
        return task.cont

    @override
    def destroy(self):
        self.__command_task.remove()
        return super().destroy()
