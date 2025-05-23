from typing import override

from direct.showbase.Loader import Loader
from panda3d.core import NodePath

from cellcrawler.character.character import Character
from cellcrawler.lib.base import inject_globals


class Player(Character):
    @override
    @inject_globals
    def _load(self, loader: Loader) -> NodePath:
        # TODO: this is temporary
        model = loader.load_model("world/wall.bam", okMissing=False)
        model.set_scale(0.5)
        model.set_color_scale((1, 1, 0, 1))
        return model
