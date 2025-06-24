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
        solid = CollisionCapsule((0, 0, 0), (0, 0, 0.01), 0.45)
        self.collision_node.add_solid(solid)
        collider = model.attach_new_node(self.collision_node)
        collider.set_python_tag("character", self)
        beam = self.create_attacking_beam(1, 3, 30)
        beam.reparent_to(model)
        return model
