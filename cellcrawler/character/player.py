import functools
from typing import final, override

from direct.showbase.DirectObject import DirectObject
from direct.showbase.Loader import Loader
from panda3d.core import CollisionCapsule, CollisionHandlerPusher, CollisionTraverser, NodePath, Vec3, MouseWatcher, WindowProperties
from direct.task.Task import TaskManager

from cellcrawler.character.character import Character
from cellcrawler.character.character_command import (
    Back,
    CommandType,
    CompositeDelta,
    Forward,
    Left,
    MovementCommand,
    Right,
    RotationCommand,
    adjust_for_hpr,
)
from cellcrawler.character.command_builder import CommandBuilder
from cellcrawler.lib import base
from cellcrawler.lib.base import RootNodes, inject_globals
from cellcrawler.lib.managed_node import ManagedNode
from direct.showbase.ShowBase import ShowBase


@final
class Player(Character):
    MOUSE_SENSITIVITY = 0.5

    @override
    @inject_globals
    def _load(self, loader: Loader, ctrav: CollisionTraverser) -> NodePath:
        # TODO: this model is temporary
        model = loader.load_model("characters/player.bam", okMissing=False)
        model.set_scale(0.5)
        model.set_color_scale((1, 1, 0, 1))
        # NOTE: don't use CollisionSphere, it can pass through walls due to an apparent bug in panda3d
        self.collision_node.add_solid(CollisionCapsule((0, 0, 0), (0, 0, 0.01), 0.7))
        collider = model.attach_new_node(self.collision_node)
        self.pusher.add_collider(collider, model)
        ctrav.add_collider(collider, self.pusher)
        return model

    def __init__(self, parent: ManagedNode | None, mouse_watcher: MouseWatcher, task_manager: TaskManager, win_properties: WindowProperties) -> None:
        self.pusher = CollisionHandlerPusher()
        self.pusher.set_horizontal(True)
        super().__init__(parent)
        self._mouse_watcher = mouse_watcher
        self._win_properties = win_properties
        
        self._base = base
        
        self.key_tracker = DirectObject()
        self.move_commands: dict[str, Vec3] = {}
        self.__is_mouse1_held = False
        self.__last_mouse_x = 0
        
        self.configure_camera()
        
        self.key_tracker.accept("mouse1", self.__start_holding_mouse1)
        self.key_tracker.accept("mouse1-up", self.__stop_holding_mouse1)
        task_manager.add(self.__update_mouse_hold, "mouse_hold")
        
        move_builder = CommandBuilder(
            CommandType.MOVE, lambda c: MovementCommand(c, adjust_for_hpr), lambda x: lambda: x, CompositeDelta
        )
        rotate_builder = CommandBuilder(CommandType.ROTATE, RotationCommand, lambda x: x, sum)
        self.key_tracker.accept("w", functools.partial(self.add_command, move_builder, "w", Forward))
        self.key_tracker.accept("a", functools.partial(self.add_command, move_builder, "a", Left))
        self.key_tracker.accept("s", functools.partial(self.add_command, move_builder, "s", Back))
        self.key_tracker.accept("d", functools.partial(self.add_command, move_builder, "d", Right))
        self.key_tracker.accept("q", functools.partial(self.add_command, rotate_builder, "q", 1))
        self.key_tracker.accept("e", functools.partial(self.add_command, rotate_builder, "e", -1))

        self.key_tracker.accept("w-up", functools.partial(self.remove_command, move_builder, "w"))
        self.key_tracker.accept("a-up", functools.partial(self.remove_command, move_builder, "a"))
        self.key_tracker.accept("s-up", functools.partial(self.remove_command, move_builder, "s"))
        self.key_tracker.accept("d-up", functools.partial(self.remove_command, move_builder, "d"))
        self.key_tracker.accept("q-up", functools.partial(self.remove_command, rotate_builder, "q"))
        self.key_tracker.accept("e-up", functools.partial(self.remove_command, rotate_builder, "e"))

    @inject_globals
    def configure_camera(self, nodes: RootNodes):
        # First-person camera
        nodes.camera.reparent_to(self.node)
        nodes.camera.set_hpr(0, 0, 0)
        nodes.camera.set_pos(0, 0, 1.5)

    def add_command[T](self, builder: CommandBuilder[T], key: str, value: T):
        command = builder.add(key, value)
        self.set_command(builder.id, command)

    def remove_command[T](self, builder: CommandBuilder[T], key: str):
        command = builder.remove(key)
        self.set_command(builder.id, command)

    @override
    def destroy(self):
        self.key_tracker.ignore("mouse_hold")
        self.key_tracker.ignore("mouse1")
        self.key_tracker.ignore("mouse1-up")
        return super().destroy()

    def __start_holding_mouse1(self):
        self.__is_mouse1_held = True

    def __stop_holding_mouse1(self):
        self.__is_mouse1_held = False
        self.set_command(CommandType.ROTATE, None)

    def __update_mouse_hold(self, task):
        if self.__is_mouse1_held:
            if self._mouse_watcher.hasMouse():
                current_x = self._mouse_watcher.getMouseX()
                delta = current_x - self.__last_mouse_x
                if abs(delta) > 0.0001:
                    rotation_speed = int(-delta * self.MOUSE_SENSITIVITY * 500)
                    self.set_command(CommandType.ROTATE, RotationCommand(rotation_speed))
                self.__last_mouse_x = current_x
        return task.cont
    
    def __get_window_center(self):
        props = self._win_properties
        return (props.get_x_size() // 2, props.get_y_size() // 2)
