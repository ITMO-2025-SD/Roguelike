import functools
import random
from typing import Final, final, override

from direct.gui.DirectLabel import DirectLabel
from direct.interval.FunctionInterval import Func
from direct.interval.LerpInterval import LerpScaleInterval
from direct.interval.MetaInterval import Sequence
from direct.showbase.DirectObject import DirectObject
from observables.observable_object import ComputedProperty, Value
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
from cellcrawler.character.character_hp_bar import CharacterHPBar
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
from cellcrawler.core.roguelike_calc_tree import LevelTree, MobDied, PlayerDied, PlayerNode
from cellcrawler.inventory.datastore import Inventory
from cellcrawler.inventory.gui import InventoryGUI
from cellcrawler.inventory.items.fear_amulet import FearAmulet
from cellcrawler.inventory.items.poisonous_helmet import PoisonousHelmet
from cellcrawler.inventory.items.speed_amulet import SpeedAmulet
from cellcrawler.inventory.items.stunning_armor import StunningArmor
from cellcrawler.lib.base import DependencyInjector, RootNodes, inject_globals
from cellcrawler.lib.managed_node import ManagedNode
from cellcrawler.lib.model_repository import models
from cellcrawler.lib.observable_utils import DirectGuiWrapper
from cellcrawler.lib.p3d_utils import toggle_vis
from cellcrawler.maze.pathfinding.character_pathfinding import CharacterPathfinding
from cellcrawler.maze.pathfinding.repeated_pathfinder import RepeatedPathfinder


@final
class Player(Character[PlayerNode]):
    DEFAULT_DAMAGE = 50
    BONUS_HP_PER_LEVEL = 25

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

    def __init__(self, parent: ManagedNode) -> None:
        self.pusher = CollisionHandlerPusher()
        self.pusher.set_horizontal(True)
        self.pathfinder = CharacterPathfinding(self)
        DependencyInjector.set_pathfinder(self.pathfinder)
        super().__init__(parent)
        self.pathfinder_service = RepeatedPathfinder(self, self.pathfinder, 1)
        self.pusher.add_collider(self.collider_np, self.node)
        self.collision_node.set_into_collide_mask(0)
        self.collision_node.set_from_collide_mask(PUSHER_COLLIDE_MASK | MOB_BEAM_COLLIDE_MASK)
        self.beam_collider.set_into_collide_mask(PLAYER_BEAM_COLLIDE_MASK)
        # QueueDebugger(self, "player", self.attacked_mobs_queue)
        # self.collision_node_pusher.set_into_collide_mask(0)
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

        self.inventory = Inventory(self.calc_node, [])
        self.inventory_gui = InventoryGUI(self, self.inventory)
        self.inventory_gui.frame.hide()
        # TODO: might need a GUI manager
        self.key_tracker.accept("i", functools.partial(toggle_vis, self.inventory_gui.frame))
        hp_bar = CharacterHPBar(self, self.health, self.max_health)

        self.experience: Final = Value(0)
        self.level: Final = Value(1)
        self.exp_to_next: Final = ComputedProperty(lambda: self.level.value * (self.level.value + 1) // 2)
        level_bar = CharacterHPBar(self, self.experience, self.exp_to_next, "EXP")
        self.experience.observe(self.update_level)
        self.level.observe(self.level_changed)
        self.calc_node.accept(MobDied, lambda: self.experience.set(self.experience.value + 1))

        root_nodes = DependencyInjector.get(RootNodes)
        hp_bar.node.reparent_to(root_nodes.bottom_left)
        hp_bar.node.set_pos(0.05, 0, 0.1)
        hp_bar.node.set_scale(0.5)
        level_bar.node.reparent_to(root_nodes.bottom_left)
        level_bar.node.set_pos(0.05, 0, 0.28)
        level_bar.node.set_scale(0.5)

        self.level_text = DirectGuiWrapper(
            DirectLabel,
            text=ComputedProperty(lambda: f"Level {self.level.value}"),
            scale=0.1,
            pos=(0.3, 0, 0.41),
            parent=root_nodes.bottom_left,
            relief=None,
        )

    def level_changed(self, _value: int):
        self.max_health.value += self.BONUS_HP_PER_LEVEL
        self.health.value = self.max_health.value

    def update_level(self, exp: int):
        if exp >= self.exp_to_next.value:
            self.level.value += 1
            self.experience.value -= exp
            self.gain_random_item()

    def gain_random_item(self):
        ctors = [PoisonousHelmet, FearAmulet, SpeedAmulet, StunningArmor]
        self.inventory.add(random.choice(ctors)())

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
        self.level_text.value.destroy()
        self.key_tracker.ignore_all()
        return super().destroy()

    def exec_attack(self):
        if self.get_command(CommandType.ATTACK) is None:
            self.set_command(CommandType.ATTACK, make_attack(self))

    @override
    def kill(self):
        Sequence(  # pyright: ignore[reportCallIssue]
            LerpScaleInterval(self.node, 0.35, 0.001),
            Func(self.destroy),
            Func(self.calc_node.dispatch, PlayerDied),
            Func(self.calc_node.destroy),
        ).start()
