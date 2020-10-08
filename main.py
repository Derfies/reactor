import random
random.seed(2, version=1)

import networkx as nx

from reactor import utils
from reactor.const import POSITION
from reactor.mapgenerator import MapGenerator


# Remaining fails:
# bow1
# reactor5 (sometimes)
GRID_PATH = 'data/reactor2.gexf'


if __name__ == '__main__':

    # Initialise a map generator using a path to a node graph file, then run it.
    gen = MapGenerator(GRID_PATH)
    gen.run()

    # Show result.
    pos = nx.get_node_attributes(gen.layouter.layout, POSITION)
    print(pos)
    utils.draw_graph(gen.layouter.layout, pos)