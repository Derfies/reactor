from operator import itemgetter

import networkx as nx

from reactor.layouter import Layouter
from reactor.map import Map
from reactor.readers.gexfreader import GEXFReader
from reactor.roomplacer import RoomPlacer


class MapGenerator(object):

    def __init__(self, grid_path):
        self._grid_path = grid_path
        self._g = nx.Graph()

    def load_graph(self):
        self._g = GEXFReader()(self._grid_path).to_undirected()

        # Ensure no node has a degree greater than 4.
        max_degree = list(filter(lambda x: x[1] > 4, self._g.degree))
        msg = 'Node(s): {} have degree greater than 4'
        assert not max_degree, msg.format(', '.join(map(itemgetter(0), max_degree)))

    def run(self):
        self.load_graph()
        map_ = Map()
        layouter = Layouter(self._g, map_)
        layouter.run()
        room_placer = RoomPlacer(self._g, map_)
        room_placer.run()
        return map_
