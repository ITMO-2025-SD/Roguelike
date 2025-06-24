import functools
from typing import final, override

from direct.showbase.DirectObject import DirectObject
from panda3d.core import (
    CollisionCapsule,
    CollisionHandlerEvent,
    CollisionHandlerPusher,
    CollisionTraverser,
    NodePath,
    Vec3,
)

from cellcrawler.character.character import (
    MOB_BEAM_COLLIDE_MASK,
    PLAYER_BEAM_COLLIDE_MASK,
    PUSHER_COLLIDE_MASK,
    Character,
    CommandType,
)
from cellcrawler.character.command_builder import CommandBuilder
from cellcrawler.character.commands import (
    Back,
    CompositeDelta,
    Forward,
    Left,
    MovementCommand,
    Right,
    RotationCommand,
    adjust_for_hpr,
    make_attack,
)
from cellcrawler.core.roguelike_calc_tree import LevelTree, PlayerNode
from cellcrawler.inventory.datastore import Inventory
from cellcrawler.inventory.gui import InventoryGUI
from cellcrawler.inventory.items.fear_amulet import FearAmulet
from cellcrawler.inventory.items.speed_amulet import SpeedAmulet
from cellcrawler.lib.base import RootNodes, inject_globals
from cellcrawler.lib.managed_node import ManagedNode
from cellcrawler.lib.model_repository import models
from cellcrawler.lib.p3d_utils import toggle_vis
from cellcrawler.maze.pathfinding.character_pathfinding import CharacterPathfinding


@final
class Player(Character[PlayerNode]):
    DEFAULT_DAMAGE = 50

    @override
    def get_collision_handler(self) -> CollisionHandlerEvent:
        return self.pusher

    @override
    @inject_globals
    def _load(self, ctrav: CollisionTraverser) -> NodePath:
        # TODO: this model is temporary
        model = models.load_model("characters/player")
        model.set_scale(0.5)
        model.get_child(0).set_color_scale((1, 1, 0, 1))
        # NOTE: don't use CollisionSphere, it can pass through walls due to an apparent bug in panda3d
        self.collision_node.add_solid(CollisionCapsule((0, 0, 0), (0, 0, 0.01), 0.7))
        beam = self.create_attacking_beam(1, 2.25, 40)
        beam.set_pos((0, 0.35, 0))
        beam.reparent_to(model)
        return model

    @override
    def create_calc_node(self, parent: LevelTree) -> PlayerNode:
        return PlayerNode(parent, self.pathfinder)

    def __init__(self, parent: ManagedNode | None) -> None:
        self.pusher = CollisionHandlerPusher()
        self.pusher.set_horizontal(True)
        self.pathfinder = CharacterPathfinding(self)
        super().__init__(parent)
        self.pusher.add_collider(self.collider_np, self.node)
        self.collision_node.set_into_collide_mask(0)
        self.collision_node.set_from_collide_mask(PUSHER_COLLIDE_MASK | MOB_BEAM_COLLIDE_MASK)
        self.beam_collider.set_into_collide_mask(PLAYER_BEAM_COLLIDE_MASK)
        # QueueDebugger(self, "player", self.attacked_mobs_queue)
        # self.collision_node_pusher.set_into_collide_mask(0)
        self.pathfinder.start()
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
        self.key_tracker.accept("space", self.exec_attack)

        self.key_tracker.accept("w-up", functools.partial(self.remove_command, move_builder, "w"))
        self.key_tracker.accept("a-up", functools.partial(self.remove_command, move_builder, "a"))
        self.key_tracker.accept("s-up", functools.partial(self.remove_command, move_builder, "s"))
        self.key_tracker.accept("d-up", functools.partial(self.remove_command, move_builder, "d"))
        self.key_tracker.accept("q-up", functools.partial(self.remove_command, rotate_builder, "q"))
        self.key_tracker.accept("e-up", functools.partial(self.remove_command, rotate_builder, "e"))

        self.inventory = Inventory(self.calc_node, [SpeedAmulet(), FearAmulet()])
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

    def exec_attack(self):
        if self.get_command(CommandType.ATTACK) is None:
            self.set_command(CommandType.ATTACK, make_attack(self))

    @override
    def kill(self):
        # TODO: temporary
        self.destroy()
