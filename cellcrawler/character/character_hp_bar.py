from typing import final, override

from direct.interval.Interval import Interval
from direct.interval.LerpInterval import LerpColorInterval, LerpScaleInterval
from direct.interval.MetaInterval import Parallel
from observables.observable_generic import ObservableObject
from panda3d.core import NodePath
from panda3d.direct import CInterval

from cellcrawler.lib.managed_node import ManagedNode, ManagedNodePath
from cellcrawler.lib.p3d_utils import lerp_color, make_node_from_vertices

TOP = 0.15
BOTTOM = -0.15
LEFT = 0  # bar starts on the left, for scaling
RIGHT = 1
INNER_DELTA = 0.02
TRANSITION_DURATION = 0.4
Y_DELTA = -0.001


@final
class CharacterHPBar(ManagedNodePath):
    def __init__(self, parent: ManagedNode, health: ObservableObject[int], max_health: ObservableObject[int]) -> None:
        self.health = health
        self.max_health = max_health
        self.interval: Interval | CInterval | None = None
        super().__init__(parent)
        self.inner_node = make_node_from_vertices(
            [
                (LEFT + INNER_DELTA, Y_DELTA, TOP - INNER_DELTA),
                (LEFT + INNER_DELTA, Y_DELTA, BOTTOM + INNER_DELTA),
                (RIGHT - INNER_DELTA, Y_DELTA, BOTTOM + INNER_DELTA),
                (RIGHT - INNER_DELTA, Y_DELTA, TOP - INNER_DELTA),
            ]
        )
        self.inner_node.reparent_to(self.node)
        self.hp_token = self.health.observe(lambda x: self.redraw())
        self.max_hp_token = self.max_health.observe(lambda x: self.redraw())
        self.inner_node.set_color(self.get_target_color())

    @property
    def hp_percentage(self):
        return self.health.value / self.max_health.value

    def get_target_color(self):
        if self.hp_percentage < 0.25:
            return lerp_color((0, 0, 0, 1), (1, 0, 0, 1), self.hp_percentage * 4)
        if self.hp_percentage < 0.5:
            return lerp_color((1, 0, 0, 1), (1, 0.7, 0, 1), self.hp_percentage * 4 - 1)
        if self.hp_percentage < 0.7:
            return lerp_color((1, 0.7, 0, 1), (0.7, 1, 0, 1), self.hp_percentage * 5 - 2.5)
        if self.hp_percentage < 0.9:
            return lerp_color((0.7, 1, 0, 1), (0, 1, 0, 1), self.hp_percentage * 5 - 3.5)
        return 0, 1, 0, 1

    def redraw(self):
        if self.interval:
            self.interval.pause()

        self.interval = Parallel(  # pyright: ignore[reportCallIssue]
            LerpColorInterval(self.inner_node, TRANSITION_DURATION, self.get_target_color(), blendType="easeInOut"),
            LerpScaleInterval(self.inner_node, TRANSITION_DURATION, (self.hp_percentage, 1, 1), blendType="easeInOut"),
        )
        self.interval.start()

    @override
    def _load(self) -> NodePath:
        return make_node_from_vertices([(LEFT, 0, TOP), (LEFT, 0, BOTTOM), (RIGHT, 0, BOTTOM), (RIGHT, 0, TOP)])

    @override
    def destroy(self):
        self.hp_token.destroy()
        self.max_hp_token.destroy()
        super().destroy()
