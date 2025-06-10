__all__ = ["models"]


from typing import final

from direct.showbase.Loader import Loader
from panda3d.core import NodePath

from cellcrawler.lib.base import RootNodes, inject_globals


@final
class ModelRepository:
    _loader: Loader | None = None
    _hidden: NodePath | None = None
    _find_cache: dict[str, NodePath]

    def __init__(self):
        self._find_cache = {}

    @inject_globals
    def init(self, loader: Loader, nodes: RootNodes):
        self._loader = loader
        self._hidden = nodes.hidden

    def _find(self, model: str, name: str):
        if not (self._loader and self._hidden):
            raise RuntimeError("model repository not yet initialized")
        if model not in self._find_cache:
            self._find_cache[model] = self._loader.load_model(model, okMissing=False)
        child = self._find_cache[model].find(name)
        if not child:
            raise ValueError(f"Cannot find {model}/{name}")
        return child.copy_to(self._hidden)

    def load_model(self, name: str):
        if not self._loader:
            raise RuntimeError("model repository not yet initialized")
        return self._loader.load_model(f"{name}.bam", okMissing=False)

    def get_item(self, name: str):
        return self._find("gui/items.bam", f"**/{name}")

    def get_gui_element(self, name: str):
        return self._find("gui/elements.bam", f"**/{name}")


models = ModelRepository()
