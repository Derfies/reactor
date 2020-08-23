import copy

from face import Face
from const import Direction, Angle
from side import Side
from vector import Vector2


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

        self.offset = offset or Vector2(0, 0)

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