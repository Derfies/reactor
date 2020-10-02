import networkx as nx

from reactor.geometry.vector import Vector2


class Face(nx.DiGraph):

    # def __init__(self, start_direction, offset=None):
    #     self.start_direction = start_direction
    #     self.offset = offset if offset is not None else Vector2(0, 0)

    @classmethod
    def from_path(cls, nodes):
        face = cls()
        nx.add_path(face, nodes)
        face.add_edge(nodes[-1], nodes[0])
        return face

    def get_source_edge(self):
        return self.graph.get('start')

    def set_source_edge(self, edge):
        assert edge in self.edges(), 'The edge {}-{} is not in the graph'.format(*edge)
        self.graph['start'] = edge

    def edges_forward(self):
        return nx.edge_dfs(self, self.get_source_edge())

    def edges_reverse(self):
        return iter([tuple(reversed(edge)) for edge in self.edges_forward()])