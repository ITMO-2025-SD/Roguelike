from collections.abc import Collection

from direct.actor.Actor import Actor
from direct.gui.DirectGuiBase import DirectGuiWidget
from direct.showbase.DirectObject import DirectObject
from panda3d.core import (
    CollisionPolygon,
    CollisionSolid,
    Geom,
    GeomNode,
    GeomTriangles,
    GeomVertexData,
    GeomVertexFormat,
    GeomVertexReader,
    GeomVertexWriter,
    LVecBase3,
    LVecBase4,
    NodePath,
    Triangulator3,
)


def cleanup_node(node: NodePath):
    if isinstance(node, Actor):
        node.cleanup()
    elif isinstance(node, DirectGuiWidget):
        node.destroy()
    else:
        node.remove_node()

    if isinstance(node, DirectObject):
        node.ignore_all()


def toggle_vis(node: NodePath):
    if node.is_hidden():
        node.show()
    else:
        node.hide()


def make_node_from_vertices(
    points: Collection[LVecBase3 | tuple[float, float, float]],
    *,
    colors: Collection[LVecBase4 | tuple[float, float, float, float]] | None = None,
):
    colors = colors or [(1, 1, 1, 1) for _ in points]
    fmt = GeomVertexFormat.getV3c4()
    vdata = GeomVertexData("polygon", fmt, Geom.UHStatic)
    vdata.setNumRows(len(points))

    vertex_writer = GeomVertexWriter(vdata, "vertex")
    color_writer = GeomVertexWriter(vdata, "color")
    triangulator = Triangulator3()
    for i, (point, color) in enumerate(zip(points, colors, strict=True)):
        vertex_writer.addData3(*point)
        color_writer.addData4(*color)
        triangulator.addVertex(*point)
        triangulator.addPolygonVertex(i)

    triangulator.triangulate()

    prim = GeomTriangles(Geom.UHStatic)
    for i in range(triangulator.getNumTriangles()):
        prim.addVertices(triangulator.getTriangleV0(i), triangulator.getTriangleV1(i), triangulator.getTriangleV2(i))
        prim.closePrimitive()

    geom = Geom(vdata)
    geom.addPrimitive(prim)
    node = GeomNode("ui_polygon")
    node.addGeom(geom)

    return NodePath(node)


def make_polyset_solids(node: GeomNode):
    """
    Creates a collider for each triangle of the node, similar to Polyset egg tag.
    Warning: using this on complex models will cause a LOT of lag at runtime as many colliders have to be considered.
    """

    colliders: list[CollisionSolid] = []
    for geom in node.get_geoms():
        reader = GeomVertexReader(geom.get_vertex_data(), "vertex")

        for raw_prim in geom.get_primitives():
            prim = raw_prim.decompose()
            for poly in range(prim.get_num_primitives()):
                s, e = prim.get_primitive_start(poly), prim.get_primitive_end(poly)
                poly_verts: list[LVecBase3] = []
                for i in range(s, e):
                    reader.set_row(prim.get_vertex(i))
                    poly_verts.append(reader.get_data3())
                colliders.append(CollisionPolygon(*poly_verts))
    return colliders


def lerp_color(
    color1: LVecBase4 | tuple[float, float, float, float],
    color2: LVecBase4 | tuple[float, float, float, float],
    mult: float,
):
    return LVecBase4(color1) * (1 - mult) + LVecBase4(color2) * mult
