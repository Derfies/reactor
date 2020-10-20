import random
from collections import deque

import networkx as nx

from reactor import utils
from reactor.blocks.faceblock import FaceBlock
from reactor.const import Angle, Direction, POSITION, WEIGHT
from reactor.geometry.rect import Rect
from reactor.geometry.vector import Vector2
from reactor.orthogonalface import OrthogonalFace


ROOM_CHANCE = 1
ROOM_MIN_WIDTH = 3
ROOM_MAX_WIDTH = 5
ROOM_MIN_HEIGHT = 3
ROOM_MAX_HEIGHT = 5


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
            if collides:
                break

        # Check that the room doesn't intersect any edges on the graph (aside
        # from the in / out edges of the node it belongs to.
        edges = set(self._map.layout.edges)
        edges -= set(self._map.layout.in_edges(node))
        edges -= set(self._map.layout.out_edges(node))
        for edge in edges:
            edge_rect = Rect(*utils.get_edge_positions(self._map.layout, edge))
            edge_rect.normalise()
            collides = collides or room.intersects(edge_rect)
            if collides:
                break

        return not collides

    def run(self):

        self.widths = {}
        self.heights = {}

        # Build rooms on all nodes at unit dimensions.
        pos = nx.get_node_attributes(self._map.layout, POSITION)
        for node in self._g.nodes:

            # TODO: Clean this up and put into settings somewhere. This tells us
            # to use different room chances per edge weight.
            room_chance = 0 if any([self._g.edges[edge].get(WEIGHT, 1) > 1 for edge in self._g.edges(node)]) else 1
            if random.random() <= room_chance:
                room = Rect(pos[node] - Vector2(0.5, 0.5), pos[node] + Vector2(0.5, 0.5))
                self.rooms[node] = room
                self.widths[node] = random.randrange(ROOM_MIN_WIDTH, ROOM_MAX_WIDTH)
                self.heights[node] = random.randrange(ROOM_MIN_HEIGHT, ROOM_MAX_HEIGHT)

        # Now attempt to grow rooms.
        nodes = deque(self._g.nodes)
        while nodes:
            node = nodes.popleft()
            room = self.rooms.get(node)
            if room is None:
                continue

            # Iterate directions and grow the rect by one unit each time.
            changed = False
            directions = list(Direction)
            random.shuffle(directions)
            for direction in directions:
                test_room = Rect(room.p1.copy(), room.p2.copy())
                if direction == Direction.UP and room.height < self.heights[node]:
                    test_room.p2[1] += 1
                elif direction == Direction.RIGHT and room.width < self.widths[node]:
                    test_room.p2[0] += 1
                elif direction == Direction.DOWN and room.height < self.heights[node]:
                    test_room.p1[1] -= 1
                elif direction == Direction.LEFT and room.width < self.widths[node]:
                    test_room.p1[0] -= 1

                # If there were no collisions, make the test room the actual
                # room.
                if self.can_place(node, test_room):
                    room = self.rooms[node] = test_room
                    changed = True

            # If the room hasn't changed then it's grown to its maximum size.
            if changed and (room.width < self.widths[node] and room.height < self.heights[node]):
                nodes.append(node)

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