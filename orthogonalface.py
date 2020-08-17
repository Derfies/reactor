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

    def __init__(self, edges, angles, lengths, direction=Direction.up):
        super(OrthogonalFace, self).__init__(edges)

        assert len(edges) == len(angles) == len(angles), 'Number of edges, angles and lengths must be equal'
        assert sum(angles) == 360, 'Face not closed: {}'.format(angles)

        self.angles = tuple(angles)
        self.lengths = lengths
        self.start_direction = direction
        self.directions = list(zip(*list(self._edge_walk())))[2]    # Gross.

        # Work out sides.
        # TODO: This could do with more clean up.
        indices = {}
        lengths = {}
        for edge_idx, edge, edge_dir in self._edge_walk():
            indices.setdefault(edge_dir, []).append(edge_idx)
            lengths.setdefault(edge_dir, []).append(self.lengths[edge_idx])
        self.sides = {}
        for dir_ in Direction:
            self.sides[dir_] = Side(dir_, indices[dir_], lengths[dir_])

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

    def get_node_positions(self):
        positions = {}
        pos = Vector2(0, 0)
        for edge_idx, edge, direction in self._edge_walk():
            positions[edge[0]] = copy.copy(pos)
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