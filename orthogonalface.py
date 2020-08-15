from face import Face
from const import Direction, Angle
from side import Side


class OrthogonalFace(Face):

    def __init__(self, edges, angles, lengths, direction=Direction.up):
        super(OrthogonalFace, self).__init__(edges)

        assert len(edges) == len(angles) == len(angles), 'Number of edges, angles and lengths must be equal'
        assert sum(angles) == 360, 'Face not closed: {}'.format(angles)

        self.angles = tuple(angles)
        self.lengths = lengths
        self.direction = direction

        self.sides = {}
        for dir_ in Direction:
            indices = []
            lengths = []
            for index in self.get_direction_indices(dir_):
                indices.append(index)
                lengths.append(self.lengths[index])
            self.sides[dir_] = Side(dir_, indices, lengths)

    def edge_walk(self):
        direction = self.direction
        for edge_idx, edge in enumerate(self.edges):
            yield edge_idx, edge, direction
            angle = self.angles[(edge_idx + 1) % len(self.angles)]
            if angle == Angle.inside:
                direction += 1
            elif angle == Angle.outside:
                direction -= 1
            direction = Direction.normalise(direction)

    def get_direction_indices(self, direction):
        return [
            edge_idx
            for edge_idx, edge, edge_dir in self.edge_walk()
            if edge_dir == direction
        ]

    def get_node_positions(self):
        positions = {}
        pos = [0, 0]
        for edge_idx, edge, direction in self.edge_walk():
            positions[edge[0]] = pos[:]
            length = self.lengths[edge_idx]# or 1
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