import functools
from typing import final, override

from direct.showbase.DirectObject import DirectObject
from direct.showbase.Loader import Loader
from panda3d.core import NodePath, Vec3

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
from cellcrawler.lib.base import inject_globals
from cellcrawler.lib.managed_node import ManagedNode


@final
class Player(Character):
    @override
    @inject_globals
    def _load(self, loader: Loader) -> NodePath:
        # TODO: this is temporary
        model = loader.load_model("world/wall.bam", okMissing=False)
        model.set_scale(0.5)
        model.set_color_scale((1, 1, 0, 1))
        return model

    def __init__(self, parent: ManagedNode | None) -> None:
        super().__init__(parent)
        self.key_tracker = DirectObject()
        self.move_commands: dict[str, Vec3] = {}

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

    def add_command[T](self, builder: CommandBuilder[T], key: str, value: T):
        command = builder.add(key, value)
        self.set_command(builder.id, command)

    def remove_command[T](self, builder: CommandBuilder[T], key: str):
        command = builder.remove(key)
        self.set_command(builder.id, command)

    @override
    def destroy(self):
        self.key_tracker.ignore_all()
        return super().destroy()
