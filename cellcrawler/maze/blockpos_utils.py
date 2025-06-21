from panda3d.core import Point3, Vec3

type Vec3Like = Point3 | Vec3

MAZE_SCALE = 2


def maze_to_world_position(x: int, y: int):
    return Vec3(x, -y, 0) * MAZE_SCALE


def world_to_maze_position(pos: Vec3Like):
    pos_scaled = pos / MAZE_SCALE
    x, minus_y = round(pos_scaled[0]), round(pos_scaled[1])
    return x, -minus_y
