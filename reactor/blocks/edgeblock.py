from reactor.blocks.blockbase import BlockBase


class EdgeBlock(BlockBase):

    @property
    def edge(self):
        return next(iter(self.edges))

    @property
    def edge_data(self):
        return self.edges[self.edge]

    @property
    def root(self):
        return self.edge[0]

    def is_adjacent(self, other):
        return set(self) & set(other)

    def sort(self, parent):
        common = set(self) & set(parent)
        source = next(iter(common))
        root = next(filter(lambda n: not self.in_edges(n), self))
        if root != source:
            self.add_edge(*reversed(self.edge), **self.edge_data)
            self.remove_edge(*self.edge)
