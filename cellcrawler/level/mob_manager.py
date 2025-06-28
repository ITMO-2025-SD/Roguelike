import dataclasses
import heapq
from typing import final, override

from direct.task.Task import Task, TaskManager

from cellcrawler.character.character import CommandType
from cellcrawler.character.mob import Mob
from cellcrawler.character.mob_factory import MobFactory
from cellcrawler.core.environment import Environment
from cellcrawler.lib.base import DependencyInjector, inject_globals
from cellcrawler.lib.managed_node import ManagedNode


@dataclasses.dataclass
class MobCommandRestart:
    time: float
    mob: Mob

    def __lt__(self, other: "MobCommandRestart"):
        return self.time < other.time


@final
class MobManager(ManagedNode):
    TASK_RESTART_DELAY = 3

    def __init__(self, parent: Environment):
        super().__init__(parent)
        task_manager = DependencyInjector.get(TaskManager)
        self.mobs: set[Mob] = set()
        self.mob_command_restarts: list[MobCommandRestart] = []
        self.__commandsetting_task = task_manager.add(self.__set_commands, "restart-mob-commands")

    def __set_commands(self, task: Task):
        time_passed = task.time
        while self.mob_command_restarts and self.mob_command_restarts[0].time <= time_passed:
            data = heapq.heappop(self.mob_command_restarts)
            if not self.set_command_for(data.mob):
                heapq.heappush(
                    self.mob_command_restarts, MobCommandRestart(time_passed + self.TASK_RESTART_DELAY, data.mob)
                )
        return task.cont

    def set_command_for(self, mob: Mob):
        if not mob.strategy:
            return False
        command = mob.strategy.make_command(mob)
        mob.set_command(CommandType.MOB_MOVEMENT, command)
        return command is not None

    def add(self, mob_: Mob):
        def set_new_command(mob: Mob, done_commands: list[CommandType]):
            if CommandType.MOB_MOVEMENT in done_commands:
                # Attempt to set the command in the next game tick
                heapq.heappush(self.mob_command_restarts, MobCommandRestart(-1, mob))

        mob_.run_on_command_done(set_new_command)
        # Also run this immediately
        heapq.heappush(self.mob_command_restarts, MobCommandRestart(-1, mob_))

    @override
    @inject_globals
    def _cleanup(self, task_mgr: TaskManager) -> None:
        task_mgr.remove(self.__commandsetting_task)


@dataclasses.dataclass
class SpawnBlackboard:
    env: Environment
    mob_mgr: MobManager
    mob_factory: MobFactory

    def spawn_random_mob_at(self, pos: tuple[int, int]):
        mob = self.mob_factory.create(self.env)
        if mob:
            mob.move_to(pos)
            self.mob_mgr.add(mob)
            self.env.spawn_mob(mob)
