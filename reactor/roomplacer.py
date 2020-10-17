import random

import networkx as nx

from reactor.blocks.faceblock import FaceBlock
from reactor.const import Angle, Direction, POSITION
from reactor.geometry.vector import Vector2
from reactor.orthogonalface import OrthogonalFace


class RoomPlacer:

    def __init__(self, g, map_):
        self._g = g
        self._map = map_

    def run(self):

        pos = nx.get_node_attributes(self._map.layout, POSITION)
        for node in self._map.layout.nodes:

            f = FaceBlock.from_path((1, 2, 3, 4))
            angles = {n: Angle.INSIDE for n in f}

            i = random.randint(1, 3)
            lengths = {e: i for e in f.edges}
            direction = Direction.UP
            offset = pos[node] - Vector2(i / 2.0, i / 2.0)
            of = OrthogonalFace(f, angles, lengths, direction, offset)

            self._map.rooms.append(of)
