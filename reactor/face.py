import networkx as nx


SOURCE_EDGE = 'source_edge'


class Face(nx.DiGraph):

    @classmethod
    def from_path(cls, nodes):
        face = cls()
        nx.add_path(face, nodes)
        face.add_edge(nodes[-1], nodes[0])
        return face

    def get_source_edge(self):
        return self.graph.get(SOURCE_EDGE)

    def set_source_edge(self, edge):
        assert edge in self.edges(), 'The edge {}-{} is not in the graph'.format(*edge)
        self.graph[SOURCE_EDGE] = edge

    def edges_forward(self):
        return nx.edge_dfs(self, self.get_source_edge())

    def edges_reverse(self):
        return iter([tuple(reversed(edge)) for edge in self.edges_forward()])