from typing import final, override

from panda3d.core import NodePath

from cellcrawler.character.mob import Mob
from cellcrawler.lib.model_repository import models


@final
class Doppelganger(Mob):
    @override
    def _load(self) -> NodePath:
        # TODO: this model is temporary
        model = models.load_model("characters/player")
        model.set_scale(0.3)
        model.set_color_scale((1, 0, 1, 1))
        return model
