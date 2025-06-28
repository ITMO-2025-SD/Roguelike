import abc
import functools
import math
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, ClassVar, Final, Generic, Self, TypeVar, cast, final, override

from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.interval.FunctionInterval import Func
from direct.interval.LerpInterval import LerpColorScaleInterval
from direct.interval.MetaInterval import Sequence
from direct.showbase.DirectObject import DirectObject
from direct.task.Task import Task, TaskManager
from observables.observable_object import Value
from panda3d.core import (
    BitMask32,
    ClockObject,
    CollisionEntry,
    CollisionHandlerEvent,
    CollisionNode,
    CollisionTraverser,
    GeomNode,
    NodePath,
    Vec4,
)

from cellcrawler.core.roguelike_calc_tree import CharacterNode, Damage, DamageContext, DamageDealt, LevelTree, MaxHealth
from cellcrawler.lib.base import DependencyInjector, inject_globals
from cellcrawler.lib.calculation_tree import Trigger
from cellcrawler.lib.managed_node import ManagedNode, ManagedNodePath
from cellcrawler.lib.model_repository import models
from cellcrawler.lib.p3d_utils import make_polyset_solids
from cellcrawler.maze.blockpos_utils import maze_to_world_position, world_to_maze_position
from cellcrawler.maze.maze_data import MazeData

CalcNodeT = TypeVar("CalcNodeT", bound=CharacterNode)

BEAM_INACTIVE_COLOR = Vec4(1, 1, 0.7, 1)
BEAM_ACTIVE_COLOR = Vec4(1, 0.2, 0.2, 1)
PUSHER_COLLIDE_MASK = BitMask32(0x0001)
PLAYER_BEAM_COLLIDE_MASK = BitMask32(0x0002)
MOB_BEAM_COLLIDE_MASK = BitMask32(0x0004)


@dataclass
class AttackContext:
    attacker: "Character[Any]"
    defender: "Character[Any]"
    damage: int


AttackHappened = Trigger[AttackContext]("AttackHappened")


class CommandType(Enum):
    MOVE = auto()
    ROTATE = auto()
    MOB_MOVEMENT = auto()
    ATTACK = auto()


class Character(ManagedNodePath, Generic[CalcNodeT], abc.ABC):
    DEFAULT_MAX_HEALTH: ClassVar[int] = 100
    DEFAULT_DAMAGE: ClassVar[int] = 20

    @abc.abstractmethod
    def get_collision_handler(self) -> CollisionHandlerEvent:
        pass

    def __init__(self, parent: ManagedNode | None) -> None:
        self.__beam: NodePath | None = None
        self.collision_node: Final = CollisionNode(f"char-{id(self)}")
        self.beam_collider: Final = CollisionNode(f"beam-{id(self)}")
        super().__init__(parent)
        self.collider_np: Final = self.node.attach_new_node(self.collision_node)

        self.calc_node: Final = self.__make_calc_node()
        self.health: Final = Value(self.calc_node.calculate(MaxHealth, self.DEFAULT_MAX_HEALTH, self.calc_node))
        self.max_health: Final = Value(self.health.value)
        self.__commands: dict[CommandType, CharacterCommand] = {}
        task_manager = DependencyInjector.get(TaskManager)
        self.__command_task = task_manager.add(self.__exec_command, f"exec-character-commands-{id(self)}")
        ctrav = DependencyInjector.get(CollisionTraverser)
        self.collider_np.set_python_tag("character", self)
        ctrav.add_collider(self.collider_np, self.get_collision_handler())
        self.__on_command_done: list[Callable[[Self, list[CommandType]], None]] = []
        self.__prev_position: tuple[int, int] = (-1, -1)
        self.__on_cell_change: list[Callable[[Self], None]] = []
        characters.add(self)

    def create_attacking_beam(self, height: float, length: float, fov: float) -> NodePath:
        """
        First NodePath is a geom node, second is a collision node.
        """
        beam = models.load_model("characters/beam")
        tan = math.tan(math.radians(fov / 2))
        beam.set_scale((length * tan, length / math.sqrt(2), height))
        beam.set_color(BEAM_INACTIVE_COLOR)
        self.__beam = beam
        colliders = make_polyset_solids(cast(GeomNode, beam.get_child(0).node()))
        for s in colliders:
            s.set_tangible(False)
            self.beam_collider.add_solid(s)
        beam_coll_node = self.__beam.attach_new_node(self.beam_collider)
        beam_coll_node.set_python_tag("beam_character", self)
        return beam

    @property
    def attacking_beam(self):
        return self.__beam

    def move_to(self, maze_pos: tuple[int, int]):
        self.node.set_pos(maze_to_world_position(*maze_pos))

    def run_on_command_done(self, func: Callable[[Self, list[CommandType]], None]):
        self.__on_command_done.append(func)

    def run_on_cell_change(self, func: Callable[[Self], None]):
        self.__on_cell_change.append(func)

    def get_cell_pos(self):
        return world_to_maze_position(self.node.get_pos())

    @inject_globals
    def __make_calc_node(self, level: LevelTree) -> CalcNodeT:
        return self.create_calc_node(level)

    @abc.abstractmethod
    def create_calc_node(self, parent: LevelTree) -> CalcNodeT:
        pass

    def get_command(self, key: CommandType):
        return self.__commands.get(key)

    def set_command(self, key: CommandType, command: "CharacterCommand | None"):
        if command is None:
            self.__commands.pop(key, None)
        else:
            self.__commands[key] = command

    def __update_occupied_position(self):
        new_position = self.get_cell_pos()
        if new_position != self.__prev_position:
            maze = DependencyInjector.get(MazeData)
            if self.__prev_position != (-1, -1):
                maze.clear_occupied(self.__prev_position)
            self.__prev_position = new_position
            maze.set_occupied(new_position)
            for cmd in self.__on_cell_change:
                cmd(self)

    def __exec_command(self, task: Task):
        removed_commands: list[CommandType] = []
        for key, command in self.__commands.items():
            command.run(self, DependencyInjector.get(ClockObject).dt)
            if command.done:
                removed_commands.append(key)
        self.__update_occupied_position()
        for key in removed_commands:
            del self.__commands[key]
        if removed_commands:
            for hook in self.__on_command_done:
                hook(self, removed_commands)
        return task.cont

    @override
    @inject_globals
    def destroy(self, ctrav: CollisionTraverser, task_mgr: TaskManager):
        task_mgr.remove(self.__command_task)
        characters.remove(self)
        ctrav.remove_collider(self.collider_np)
        return super().destroy()

    def attack(self, other: "Character[Any]") -> None:
        ctx = DamageContext(self.calc_node, other.calc_node, self.DEFAULT_DAMAGE)
        damage = ctx.damage = self.calc_node.calculate(Damage, self.DEFAULT_DAMAGE, ctx)
        if damage > 0 and other.set_attacked(damage):
            self.calc_node.dispatch(DamageDealt, ctx)
            self.calc_node.dispatch(AttackHappened, AttackContext(self, other, damage))

    def set_attacked(self, damage: int):
        if self.health.value <= 0:
            # Already dead, the animation didn't finish yet probably.
            return False
        self.health.value -= damage
        Sequence(  # pyright: ignore[reportCallIssue]
            LerpColorScaleInterval(self.node, 0.1, (0.55, 0, 0, 1)),
            Func(self.kill) if self.health.value <= 0 else LerpColorScaleInterval(self.node, 0.4, (1, 1, 1, 1)),
        ).start()
        return True

    @abc.abstractmethod
    def kill(self):
        pass


class CharacterCommand(abc.ABC):
    done: bool = False

    def set_done(self):
        self.done = True

    @abc.abstractmethod
    def run(self, character: Character[Any], dt: float) -> None:
        pass


@final
class CollisionExchanger(DirectObject):
    """
    When collision nodes for the characters and their beams are created, each collider contains the characters
    that are *attacking* the given one. This is because the character beam uses polygon collisions and thus
    can only be used as an INTO node, not as a FROM node.
    This is, unfortunately, usually not intended as we need to know what the *given character* is attacking.

    CollisionExchanger is the solution to this problem. It is a global object maintaining sets of characters
    that are attacked by each character. Each character should register itself as well as its attacking beam
    with the exchanger, and anyone can make a query of type "what is character X attacking".
    """

    notify = directNotify.newCategory("CollisionExchanger")

    EXCHANGER_IN_EVENT = "exchanger-in"
    EXCHANGER_OUT_EVENT = "exchanger-out"

    def __init__(self) -> None:
        super().__init__()

        self.attacking_map: dict[int, set[Character[Any]]] = defaultdict(set)
        self.attacked_by_map: dict[int, set[Character[Any]]] = defaultdict(set)
        self.accept(self.EXCHANGER_IN_EVENT, functools.partial(self.becomes_attack_target, True))
        self.accept(self.EXCHANGER_OUT_EVENT, functools.partial(self.becomes_attack_target, False))

    def manage(self, handler: CollisionHandlerEvent):
        handler.add_in_pattern(self.EXCHANGER_IN_EVENT)
        handler.add_out_pattern(self.EXCHANGER_OUT_EVENT)

    def unmanage(self, character: Character[Any]):
        for char in self.attacked_by_map[id(character)]:
            self.attacking_map[id(char)].discard(character)
        for char in self.attacking_map[id(character)]:
            self.attacked_by_map[id(char)].discard(character)

        del self.attacking_map[id(character)]
        del self.attacked_by_map[id(character)]

    def get_attacked_chars(self, char: Character[Any]):
        return self.attacking_map.get(id(char), set())

    def becomes_attack_target(self, is_in: bool, entry: CollisionEntry):
        attacker = entry.get_into_node_path().get_python_tag("beam_character")
        defender = entry.get_from_node_path().get_python_tag("character")
        if not isinstance(attacker, Character):
            # The attacker can be a wall, the underlying system can't differentiate between the two
            # self.notify.warning(f"Expected the attacker to be a character, but got {attacker}")
            return
        elif not isinstance(defender, Character):
            self.notify.warning(f"Expected the defender to be a character, but got {defender}")
        else:
            attacker = cast(Character[Any], attacker)
            defender = cast(Character[Any], defender)
            if is_in:
                self.attacking_map[id(attacker)].add(defender)
                self.attacked_by_map[id(defender)].add(attacker)
            else:
                self.attacking_map[id(attacker)].discard(defender)
                self.attacked_by_map[id(defender)].discard(attacker)


@final
class CharacterRepository:
    def __init__(self) -> None:
        self.__chars: set[Character[Any]] = set()
        self.collisions = CollisionExchanger()

    def add(self, char: Character[Any]):
        self.__chars.add(char)
        self.collisions.manage(char.get_collision_handler())

    def remove(self, char: Character[Any]):
        self.__chars.discard(char)
        self.collisions.unmanage(char)

    def all(self):
        return list(self.__chars)


characters = CharacterRepository()
