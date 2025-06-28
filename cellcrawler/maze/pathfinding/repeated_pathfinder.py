from typing import Final, final, override

from direct.task.Task import Task, TaskManager

from cellcrawler.lib.base import inject_globals
from cellcrawler.lib.managed_node import ManagedNode
from cellcrawler.maze.pathfinding.pathfinding import PathfindingService


@final
class RepeatedPathfinder(ManagedNode):
    def __init__(self, parent: "ManagedNode | None", pathfinder: PathfindingService, period: float) -> None:
        super().__init__(parent)
        self.pathfinder = pathfinder
        self.task = None
        self.period: Final = period

    @inject_globals
    def start(self, task_mgr: TaskManager):
        if self.task:
            raise RuntimeError("Attempt to start RepeatedPathfinder twice")
        self.pathfinder.run()
        self.task = task_mgr.do_method_later(self.period, self.run, f"pathfinding-{id(self)}")

    def run(self, task: Task):
        self.pathfinder.run()
        return task.again

    @override
    @inject_globals
    def _cleanup(self, task_mgr: TaskManager) -> None:
        if self.task:
            task_mgr.remove(self.task)
            self.task = None
