import enum
import random
from collections import defaultdict

import networkx as nx
from simple_settings import settings

from reactor import utils
from reactor.const import Direction, Angle, ANGLE, LENGTH, DIRECTION, WEIGHT
from reactor.blocks.faceblock import FaceBlock
from reactor.geometry.vector import Vector2


class SideState(enum.IntEnum):

    UNKNOWN = 0
    KNOWN = 2


class Side(object):

    def __init__(self, g):
        self.g = g

        # Cache some random edge lengths.
        # TODO: We do this in a few places. Still need to find a home for this.
        self.rand_edges = []
        for edge in self.g.edges:
            edge_weight = self.g.edges[edge].get(WEIGHT, 1)
            edge_settings = settings.EDGE_WEIGHTS[edge_weight]
            self.rand_edges.append(random.randrange(
                edge_settings['MIN_LENGTH'],
                edge_settings['MAX_LENGTH'] + 1,
                edge_settings['STEP_LENGTH'])
            )

    @property
    def lengths(self):
        return [self.g.edges[e].get(LENGTH) for e in self.g.edges]

    @property
    def state(self):
        return SideState.UNKNOWN if self.num_unknown_edges else SideState.KNOWN

    @property
    def length(self):
        return sum(self.lengths)

    @property
    def known_length(self):
        return sum([l or 0 for l in self.lengths])

    @property
    def proposed_length(self):
        return sum([l or self.rand_edges[i] for i, l in enumerate(self.lengths)])

    @property
    def num_unknown_edges(self):
        return self.lengths.count(None)


class OrthogonalFace(FaceBlock):

    def __init__(self, face, angles, lengths, direction, offset=None):
        super(OrthogonalFace, self).__init__(face)

        # Important! Set the source edge the same as the given face.
        if face.source_edge is not None:
            self.source_edge = face.source_edge

        self.start_direction = direction
        self.offset = offset if offset is not None else Vector2(0, 0)

        # Set node and edge data.
        nx.set_node_attributes(self, angles, ANGLE)
        nx.set_edge_attributes(self, lengths, LENGTH)
        nx.set_edge_attributes(self, dict(self._edge_walk()), DIRECTION)

        # Calculate sides.
        self.sides = self._calculate_sides()

    def _edge_walk(self):
        direction = self.start_direction
        for edge in self.edges_forward:
            yield edge, direction
            angle = self.nodes[edge[1]][ANGLE]
            if angle == Angle.INSIDE:
                direction += 1
            elif angle == Angle.OUTSIDE:
                direction -= 1
            direction = Direction.normalise(direction)

    def _calculate_sides(self):
        edges = defaultdict(list)
        for edge in self.edges:
            edges[self.edges[edge][DIRECTION]].append(edge)
        return {
            dir_: Side(nx.DiGraph(self).edge_subgraph(edges))
            for dir_, edges in edges.items()
        }

    @property
    def node_positions(self):
        positions = {}
        pos = Vector2(0, 0)
        for edge, direction in self._edge_walk():
            positions[edge[0]] = pos + self.offset
            pos += utils.step(direction, self.edges[edge][LENGTH])
        return positions
