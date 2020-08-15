from const import SideState


class Side(object):

    def __init__(self, direction, indices, lengths):
        self.direction = direction

        assert len(indices) == len(lengths), 'Number of indices and lengths must be equal'
        self.indices = tuple(indices)
        self.lengths = tuple(lengths)

    @property
    def state(self):
        state = SideState.known
        if None in self.lengths:
            state = SideState.unknown
        return state

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