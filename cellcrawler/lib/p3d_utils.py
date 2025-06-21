from direct.actor.Actor import Actor
from direct.gui.DirectGuiBase import DirectGuiWidget
from direct.showbase.DirectObject import DirectObject
from panda3d.core import CollisionPolygon, CollisionSolid, GeomNode, GeomVertexReader, LVecBase3, NodePath


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
