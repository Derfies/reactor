import random

import networkx as nx

from reactor import utils
from reactor.blocks.faceblock import FaceBlock
from reactor.const import Angle, Direction, POSITION
from reactor.geometry.rect import Rect
from reactor.geometry.vector import Vector2
from reactor.orthogonalface import OrthogonalFace


ROOM_CHANCE = 0.35


class RoomPlacer:

    def __init__(self, g, map_):
        self._g = g
        self._map = map_

        self.rooms = {}

    def can_place(self, node, room):

        collides = False

        # Thest that the given room doesn't intersect with any other room.
        for onode in self._map.layout.nodes:
            if node == onode:
                continue
            oroom = self.rooms.get(onode)
            if oroom is None:
                continue
            collides = collides or room.intersects(oroom)
            # if node == 'N5':
            #     print('        OROOM:', oroom, collides)
            if collides:
                break

        # Check that the room doesn't intersect any edges on the graph (aside
        # from the in / out edges of the node it belongs to.
        edges = set(self._map.layout.edges)
        # if node == 'N5':
        #     print('    ALL EDGES:', edges)
        edges -= set(self._map.layout.in_edges(node))
        edges -= set(self._map.layout.out_edges(node))
        # if node == 'N5':
        #     print('    REM:', set(self._map.layout.edges(node)))
        for edge in edges:
            edge_rect = Rect(*utils.get_edge_positions(self._map.layout, edge))
            edge_rect.normalise()
            collides = collides or room.intersects(edge_rect)
            # if node == 'N5':
            #     print('        EDGE:', edge, collides)
            if collides:
                break

        return not collides

    def run(self):

        # Build rooms on all nodes at unit dimensions.
        pos = nx.get_node_attributes(self._map.layout, POSITION)
        for node in self._g.nodes:
            if random.random() > ROOM_CHANCE:
                room = Rect(pos[node] - Vector2(0.5, 0.5), pos[node] + Vector2(0.5, 0.5))
                self.rooms[node] = room

        # Now attempt to grow rooms.
        for node in self._g.nodes:
            room = self.rooms.get(node)
            if room is None:
                continue

            # Iterate directions and grow the rect by one unit each time.
            for direction in list(Direction):
                test_room = Rect(room.p1.copy(), room.p2.copy())
                if direction == Direction.UP:
                    test_room.p2[1] += 1
                elif direction == Direction.RIGHT:
                    test_room.p2[0] += 1
                elif direction == Direction.DOWN:
                    test_room.p1[1] -= 1
                elif direction == Direction.LEFT:
                    test_room.p1[0] -= 1

                # If there were no collisions, make the test room the actual
                # room.
                if self.can_place(node, test_room):
                    room = self.rooms[node] = test_room

        # Convert to polygons.
        for node in self._g.nodes:
            room = self.rooms.get(node)
            if room is None:
                continue

            f = FaceBlock.from_path((1, 2, 3, 4))
            angles = {n: Angle.INSIDE for n in f}
            lengths = {}
            lengths[(1, 2)] = lengths[(3, 4)] = room.height
            lengths[(2, 3)] = lengths[(4, 1)] = room.width
            direction = Direction.UP
            self._map.rooms.append(OrthogonalFace(f, angles, lengths, direction, room.p1))