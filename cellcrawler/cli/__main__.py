import os

from doit.api import DoitMain, ModuleTaskLoader
from panda_utils.assetpipeline import composer
from typer import Typer

app = Typer()


@app.command()
def assets(force: bool = False):
    """Builds assets required to launch the game."""

    os.chdir("resources/models")
    composer.resolve_cwd("targets.yml")
    composer.load_from_file("targets.yml", {composer.YAML_CONFIG_FILENAME})
    DoitMain(ModuleTaskLoader(composer)).run(["rebuild" if force else "build"])


if __name__ == "__main__":
    app()
