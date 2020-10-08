from operator import itemgetter

import networkx as nx

from reactor.layouter import Layouter
from reactor.readers.gexfreader import GEXFReader


class MapGenerator(object):

    def __init__(self, grid_path):
        self.grid_path = grid_path
        self._g = nx.Graph()

    @property
    def g(self):
        return self._g

    def load_graph(self):
        self._g = GEXFReader()(self.grid_path).to_undirected()

        # Ensure no node has a degree greater than 4.
        max_degree = list(filter(lambda x: x[1] > 4, self._g.degree))
        msg = 'Node(s): {} have degree greater than 4'
        assert not max_degree, msg.format(', '.join(map(itemgetter(0), max_degree)))

    def run(self):
        self.load_graph()
        self.layouter = Layouter(self.g)
        self.layouter.run()