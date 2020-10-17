import networkx as nx

from reactor.blocks.blockbase import BlockBase


SOURCE_EDGE = 'source_edge'


class FaceBlock(BlockBase):

    @classmethod
    def from_path(cls, nodes):
        face = cls()
        nx.add_path(face, nodes)
        face.add_edge(nodes[-1], nodes[0])
        nx.freeze(face)
        return face

    def __str__(self):
        return str(list(self.edges_forward))

    @property
    def root(self):
        return self.source_edge[0]

    def is_adjacent(self, other):
        if isinstance(other, self.__class__):
            other_edges = [tuple(reversed(e)) for e in other.edges]
            return set(self.edges) & set(other_edges)
        return set(self) & set(other)

    def sort(self, parent):
        if isinstance(parent, self.__class__):
            common = set(self.edges_forward) & set(parent.edges_reverse)
            self.source_edge = next(iter(common))
        else:
            common = set(self) & set(parent)
            source = next(iter(common))
            edge = next(filter(lambda e: e[0] == source, self.edges))
            self.source_edge = edge

    @property
    def source_edge(self):
        return self.graph.get(SOURCE_EDGE)

    @source_edge.setter
    def source_edge(self, edge):
        assert edge in self.edges, 'The edge {}-{} is not in the graph'.format(*edge)
        self.graph[SOURCE_EDGE] = edge

    @property
    def edges_forward(self):
        return nx.edge_dfs(self, self.source_edge)

    @property
    def edges_reverse(self):
        return iter([tuple(reversed(edge)) for edge in self.edges_forward])
