from const import SideState


class Side(object):

    def __init__(self, direction, face):
        self.direction = direction

        self.indices = [
            idx
            for idx, node in enumerate(face.nodes)
            if face.directions[idx] == direction
        ]
        self.lengths = tuple(face.lengths[idx] for idx in self.indices)

        self.face = face

    @property
    def state(self):
        return SideState.unknown if None in self.lengths else SideState.known

    @property
    def length(self):
        return sum(self.lengths)

    @property
    def known_length(self):
        return sum([l or 0 for l in self.lengths])

    @property
    def proposed_length(self):
        return sum([l or 1 for l in self.lengths])

    @property
    def num_unknown_edges(self):
        return self.lengths.count(None)