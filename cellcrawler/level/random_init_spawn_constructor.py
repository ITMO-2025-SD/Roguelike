import random

from cellcrawler.level.mob_manager import SpawnBlackboard
from cellcrawler.lib.base import DependencyInjector
from cellcrawler.maze.maze_data import MazeData


def random_init_spawn_constructor(target_mob_count: int, blackboard: SpawnBlackboard):
    # We do not have any persistent data, so we don't need to return a managed node
    maze = DependencyInjector.get(MazeData)
    bad_positions = set(maze.occupations)
    open_positions = list(set(blackboard.env.open_positions) - set(bad_positions))
    chosen_positions = random.sample(open_positions, min(target_mob_count, len(open_positions)))
    for i in chosen_positions:
        blackboard.spawn_random_mob_at(i)
