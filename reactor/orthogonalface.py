import copy

#from face import Face
from const import Direction, Angle
from side import Side
from reactor.geometry.vector import Vector2


class Face(object):

    def __init__(self, edges):
        self.edges = tuple(edges)

    @classmethod
    def from_nodes(cls, nodes):
        # Each node is the head of the edge of the same index.
        return cls([
            (nodes[idx], nodes[(idx + 1) % len(nodes)])
            for idx in range(len(nodes))
        ])

    @property
    def nodes(self):
        nodes = []
        for edge in self:
            nodes.extend(filter(lambda n: n not in nodes, edge))
        return tuple(nodes)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return set(self.edges) == set(other.edges)
        return False

    def __str__(self):
        return 'Face: ' + str(self.edges)

    def __len__(self):
        return len(self.edges)

    def __getitem__(self, idx):
        return self.edges[idx]

    def index(self, edge):
        return self.edges.index(edge)

    def reversed(self):
        """
        Note this only reverses the direction of the face edges the edge indices
        remain unchanged.

        """
        return Face([tuple(reversed(edge)) for edge in self])

    def set_from_edge(self, edge):
        idx = self.index(edge)
        edges = list(self[idx:])
        edges.extend(self[:idx])
        return self.__class__(edges)


class OrthogonalFace(Face):

    """
    TODO: Sometimes we store data by order, sometimes by dict. Seems confusing.

    Directions should be easy to turn into a list.
    """

    def __init__(self, edges, angles, lengths, direction=Direction.up, offset=None):
        super(OrthogonalFace, self).__init__(edges)

        assert len(edges) == len(angles) == len(angles), 'Number of edges, angles and lengths must be equal'
        assert sum(angles) == 360, 'Face not closed: {}'.format(angles)

        self.angles = tuple(angles)
        self.lengths = lengths
        self.start_direction = direction
        self.directions = list(zip(*list(self._edge_walk())))[2]    # Gross.

        self.offset = offset if offset is not None else Vector2(0, 0)

        self._pos = None

        # Work out sides.
        # TODO: This could do with more clean up.
        self.sides = {
            dir_: Side(dir_, self)
            for dir_ in Direction
        }

    @property
    def positions(self):
        if self._pos is None:
            self._pos = self._calculate_node_positions()
        return self._pos

    def _edge_walk(self):
        direction = self.start_direction
        for edge_idx, edge in enumerate(self.edges):
            yield edge_idx, edge, direction
            angle = self.angles[(edge_idx + 1) % len(self.angles)]
            if angle == Angle.inside:
                direction += 1
            elif angle == Angle.outside:
                direction -= 1
            direction = Direction.normalise(direction)

    def _calculate_node_positions(self):
        positions = []
        pos = Vector2(0, 0)
        for edge_idx, edge, direction in self._edge_walk():
            positions.append(copy.copy(pos) + self.offset)
            length = self.lengths[edge_idx]
            if direction == Direction.up:
                pos[1] += length
            elif direction == Direction.right:
                pos[0] += length
            elif direction == Direction.down:
                pos[1] -= length
            elif direction == Direction.left:
                pos[0] -= length
            else:
                raise Exception('Unknown direction: {}'.format(direction))
        return positions