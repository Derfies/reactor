import random
#random.seed(1)

from reactor import utils
from reactor.mapgenerator import MapGenerator

from reactor.geometry.vector import Vector2, Vector3, Vector4
from reactor.geometry.matrix import Matrix4
from reactor.wip.rect_decomp import decompose_region
from reactor.blocks.faceblock import FaceBlock
import matplotlib.pyplot as plt
from reactor.geometry.rect import Rect
from reactor import const

from reactor import utils

from reactor.wip.bspregions import BspRegions


# Remaining fails:
# bow1
# single_node1
GRID_PATH = 'data/city2.gexf'
import copy
INSET_SIZE = 6


class Volume(object):

    """All xform manipulation is done in local space."""

    def __init__(self, x=1, y=1, z=1, matrix=None):
        self.dimensions = Vector4(x, y, z, 0)
        self.matrix = matrix if matrix is not None else Matrix4()

    @classmethod
    def from_volume(cls, v):
        return cls(
            v.dimensions.x,
            v.dimensions.y,
            v.dimensions.z,
            copy.copy(v.matrix)
        )

    # @classmethod
    # def from_dimensions(cls, d):
    #     return cls(d.x, d.y, d.z)

    def __str__(self):
        str_ = '<Volume x={} y={} z={} matrix=\n{}>'
        return str_.format(
            self.dimensions.x,
            self.dimensions.y,
            self.dimensions.z,
            self.matrix
        )


if __name__ == '__main__':

    from reactor.renderers.panda3d import App

    app = App()



    gen = MapGenerator(GRID_PATH)
    map_ = gen.run()


    #print(list(map_.bg))

    for block in map_.bg:

        if not isinstance(block, FaceBlock):
            continue

        node_to_dir = {}
        for edge in block.edges_forward:
            dir_ = map_.layout.edges[edge].get(const.DIRECTION)
            node_to_dir.setdefault(edge[0], set()).add(dir_)
            node_to_dir.setdefault(edge[1], set()).add(dir_)

        region = []
        for n in block.nodes_forward:
            node_pos = utils.get_node_position(map_.layout, n)
            new_node_pos = node_pos.copy()

            for dir_ in node_to_dir[n]:
                if dir_ == const.Direction.UP:
                    new_node_pos += Vector2(INSET_SIZE, 0)
                elif dir_ == const.Direction.RIGHT:
                    new_node_pos += Vector2(0, -INSET_SIZE)
                elif dir_ == const.Direction.DOWN:
                    new_node_pos += Vector2(-INSET_SIZE, 0)
                elif dir_ == const.Direction.LEFT:
                    new_node_pos += Vector2(0, INSET_SIZE)

            region.append(list(new_node_pos))

            #print(n, node_pos, node_to_dir[n], '->', new_node_pos)

        #print(region)

        rectangles = decompose_region([region], True)


        # Plot result.
       # utils.init_pyplot((10, 10))
        for points in rectangles:
            p1 = Vector2(points[0][0], points[0][1])#+ Vector2(0.5, 0.5)
            p2 = Vector2(points[1][0], points[1][1])# - Vector2(0.5, 0.5)
            r = Rect(p1, p2)
            bsp = BspRegions(60)
            for leaf in bsp.run(r):
                map_.rooms.append(leaf)

                # print(leaf.width)
                # print(leaf.height)


                h = random.randint(20, 80)

                m = Matrix4()
                print((leaf.centre[0], 0, leaf.centre[1]))
                m.translate((leaf.centre[0], leaf.centre[1], h / 2.0))

                v = Volume(
                    leaf.width,#leaf.p1.x + leaf.width / 2,
                    leaf.height,#leaf.p1.y + leaf.height / 2,
                    h,#,
                    m
                )
                app.create_box(v)

            #map_.rooms.append(r)


    #utils.draw_map(map_)

    #v = Volume(10, 20, 30)
    #app.create_box(v)
    app.run()