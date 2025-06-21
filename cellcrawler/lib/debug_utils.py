from typing import final, override

from direct.task.Task import Task, TaskManager
from panda3d.core import CollisionHandlerQueue

from cellcrawler.lib.base import DependencyInjector, inject_globals
from cellcrawler.lib.managed_node import ManagedNode


@final
class QueueDebugger(ManagedNode):
    def __init__(self, parent: "ManagedNode | None", name: str, queue: CollisionHandlerQueue) -> None:
        super().__init__(parent)
        self.name = name
        self.queue = queue
        task_mgr = DependencyInjector.get(TaskManager)
        self.task = task_mgr.do_method_later(1, self.print_queue, f"print-queue-{id(self)}")

    def print_queue(self, task: Task):
        print(self.name, self.queue.get_entries())  # noqa: T201
        return task.again

    @override
    @inject_globals
    def _cleanup(self, task_mgr: TaskManager) -> None:
        task_mgr.remove(self.task)
