import functools
from typing import final, override

from direct.showbase.DirectObject import DirectObject
from direct.showbase.Loader import Loader
from panda3d.core import NodePath, Vec3

from cellcrawler.character.character import Character
from cellcrawler.character.movement_command import (
    Back,
    CompositeDelta,
    Forward,
    Left,
    MovementCommand,
    Right,
    adjustForHpr,
    RotationCommand,
    CommandType
)
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
        self.key_tracker.accept("w", functools.partial(self.add_move_command, "w", Forward))
        self.key_tracker.accept("a", functools.partial(self.add_move_command, "a", Left))
        self.key_tracker.accept("s", functools.partial(self.add_move_command, "s", Back))
        self.key_tracker.accept("d", functools.partial(self.add_move_command, "d", Right))

        self.key_tracker.accept("q", functools.partial(self.add_command, CommandType.ROTATE, 1))
        self.key_tracker.accept("e", functools.partial(self.add_command, CommandType.ROTATE, -1))

        self.key_tracker.accept("w-up", functools.partial(self.remove_move_command, "w"))
        self.key_tracker.accept("a-up", functools.partial(self.remove_move_command, "a"))
        self.key_tracker.accept("s-up", functools.partial(self.remove_move_command, "s"))
        self.key_tracker.accept("d-up", functools.partial(self.remove_move_command, "d"))

        self.key_tracker.accept("q-up", functools.partial(self.remove_command, CommandType.ROTATE))
        self.key_tracker.accept("e-up", functools.partial(self.remove_command, CommandType.ROTATE))

    def add_move_command(self, key: str, vec: Vec3):
        self.move_commands[key] = vec
        self.update_move_command()

    def add_command(self, type: CommandType, *args):
        if type == CommandType.ROTATE:
            self.set_command(type, RotationCommand(*args))

    def remove_move_command(self, key: str):
        self.move_commands.pop(key, None)
        self.update_move_command()

    def remove_command(self, type: CommandType):
        self.exclude_command(type)
            
    def update_move_command(self):
            if len(self.move_commands) == 0:
                self.exclude_command(CommandType.MOVE)
            elif len(self.move_commands) == 1:
                vec = list(self.move_commands.values())[0]
                self.set_command(CommandType.MOVE, MovementCommand(lambda: vec, adjustForHpr))
            else:
                vecs = list(self.move_commands.values())
                self.set_command(CommandType.MOVE, MovementCommand(CompositeDelta(vecs), adjustForHpr))

    @override
    def destroy(self):
        self.key_tracker.ignore_all()
        return super().destroy()
