import random
random.seed(8)

import networkx as nx

from reactor import utils
from reactor.const import POSITION
from reactor.mapgenerator import MapGenerator


# Remaining fails:
# bow1
# cross1 - Weirdness with face calculations...?
GRID_PATH = 'data/test12.gexf'


if __name__ == '__main__':

    # Initialise a map generator using a path to a node graph file, then run it.
    gen = MapGenerator(GRID_PATH)
    gen.run()

    # Show result.
    pos = nx.get_node_attributes(gen.layouter.layout, POSITION)
    utils.draw_graph(gen.layouter.layout, pos)