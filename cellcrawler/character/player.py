import functools
from typing import final, override

from direct.showbase.DirectObject import DirectObject
from direct.showbase.Loader import Loader
from panda3d.core import CollisionCapsule, CollisionHandlerPusher, CollisionTraverser, NodePath, Vec3

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
from cellcrawler.core.roguelike_calc_tree import LevelTree, PlayerNode
from cellcrawler.inventory.datastore import Inventory
from cellcrawler.inventory.gui import InventoryGUI
from cellcrawler.inventory.items.speed_amulet import SpeedAmulet
from cellcrawler.lib.base import RootNodes, inject_globals
from cellcrawler.lib.managed_node import ManagedNode
from cellcrawler.lib.p3d_utils import toggle_vis


@final
class Player(Character[PlayerNode]):
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

    @override
    def create_calc_node(self, parent: LevelTree) -> PlayerNode:
        return PlayerNode(parent)

    def __init__(self, parent: ManagedNode | None) -> None:
        self.pusher = CollisionHandlerPusher()
        self.pusher.set_horizontal(True)
        super().__init__(parent)
        self.key_tracker = DirectObject()
        self.move_commands: dict[str, Vec3] = {}

        self.configure_camera()

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

        self.inventory = Inventory(self.calc_node, [SpeedAmulet()])
        self.inventory_gui = InventoryGUI(self, self.inventory)
        self.inventory_gui.frame.hide()
        # TODO: might need a GUI manager
        self.key_tracker.accept("i", functools.partial(toggle_vis, self.inventory_gui.frame))

    @inject_globals
    def configure_camera(self, nodes: RootNodes):
        # Rudimentary camera looking down. Should adjust placement later.
        nodes.camera.reparent_to(self.node)
        nodes.camera.set_hpr(0, -90, 0)
        nodes.camera.set_pos(0, 0, 15)

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
