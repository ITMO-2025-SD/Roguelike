from typing import final, override

from panda3d.core import CollisionCapsule, NodePath

from cellcrawler.character.mob import Mob
from cellcrawler.lib.model_repository import models


@final
class Doppelganger(Mob):
    @override
    def _load(self) -> NodePath:
        # TODO: this model is temporary
        model = models.load_model("characters/player")
        model.set_scale(0.3)
        model.get_child(0).set_color_scale((1, 0, 1, 1))
        self.collision_node.add_solid(CollisionCapsule((0, 0, 0), (0, 0, 0.01), 0.45))
        model.attach_new_node(self.collision_node)
        beam = self.create_attacking_beam(1, 1.7, 30)
        beam.reparent_to(model)
        return model
