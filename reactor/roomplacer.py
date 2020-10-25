import random
from collections import deque

import networkx as nx
from simple_settings import settings

from reactor import utils
from reactor.const import Direction, POSITION, WEIGHT
from reactor.geometry.rect import Rect
from reactor.geometry.vector import Vector2


class Room(Rect):

    def __init__(self, pos, g, node):
        super(Room, self).__init__(pos - Vector2(0.5, 0.5), pos + Vector2(0.5, 0.5))

        edge_weight = max([
            g.edges[edge].get(WEIGHT, 1)
            for edge in g.edges(node)]
        )
        edge_settings = settings.EDGE_WEIGHTS[edge_weight]
        self.max_width = random.randrange(
            edge_settings['ROOM_MIN_WIDTH'],
            edge_settings['ROOM_MAX_WIDTH']
        )
        self.max_height = random.randrange(
            edge_settings['ROOM_MIN_HEIGHT'],
            edge_settings['ROOM_MAX_HEIGHT']
        )


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

        # Build rooms on all nodes at unit dimensions.
        pos = nx.get_node_attributes(self._map.layout, POSITION)
        for node in self._g.nodes:

            # Edge weight for a node is the max of all incident edges.
            edge_weight = max([self._g.edges[edge].get(WEIGHT, 1) for edge in self._g.edges(node)])
            edge_settings = settings.EDGE_WEIGHTS[edge_weight]

            # TODO: Clean this up and put into settings somewhere. This tells us
            # to use different room chances per edge weight.
            if random.random() <= edge_settings['ROOM_CHANCE']:
                self.rooms[node] = Room(pos[node], self._g, node)

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
                if direction == Direction.UP and room.height < room.max_height:
                    test_room.p2[1] += 1
                elif direction == Direction.RIGHT and room.width < room.max_width:
                    test_room.p2[0] += 1
                elif direction == Direction.DOWN and room.height < room.max_height:
                    test_room.p1[1] -= 1
                elif direction == Direction.LEFT and room.width < room.max_width:
                    test_room.p1[0] -= 1

                # If there were no collisions, make the test room the actual
                # room.
                if self.can_place(node, test_room):
                    room.p1.x = test_room.p1.x
                    room.p1.y = test_room.p1.y
                    room.p2.x = test_room.p2.x
                    room.p2.y = test_room.p2.y
                    changed = True

            # If the room hasn't changed then it's grown to its maximum size.
            if changed and (room.width < room.max_width and room.height < room.max_height):
                nodes.append(node)
            else:
                self._map.rooms.append(room)
