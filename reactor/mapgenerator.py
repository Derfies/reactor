from operator import itemgetter

import networkx as nx

from orthogonallayouter import OrthogonalLayouter


class MapGenerator(object):

    def __init__(self, grid_path):
        self.grid_path = grid_path
        self._g = nx.Graph()

    @property
    def g(self):
        return self._g

    def load_graph(self):
        self._g = nx.read_graphml(self.grid_path).to_undirected()

        # Ensure no node has a degree greater than 4.
        max_degree = filter(lambda x: x[1] > 4, self._g.degree)
        msg = 'Node(s): {} have degree greater than 4'
        assert not max_degree, msg.format(', '.join(map(itemgetter(0), max_degree)))

    def run(self):
        self.load_graph()
        self.layouter = OrthogonalLayouter(self.g)
        self.layouter.run()