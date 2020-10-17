import os
import random
random.seed(0)

import networkx as nx

from reactor import utils
from reactor.const import POSITION
from reactor.mapgenerator import MapGenerator


NUM_PERMUTATIONS = 20
GRID_PATH = 'data/reactor5.gexf'


if __name__ == '__main__':

    for i in range(NUM_PERMUTATIONS):

        # Set random seed and run map generator.
        random.seed(i)
        gen = MapGenerator(GRID_PATH)
        gen.run()

        # Resolve output path name.
        dir_name = os.path.splitext(os.path.split(GRID_PATH)[-1])[0]
        file_name = '{0:03d}'.format(i)
        file_path = os.path.join('output', dir_name, file_name) + '.png'

        # Save graph to file.
        pos = nx.get_node_attributes(gen.layouter.layout, POSITION)
        utils.save_graph(gen.layouter.layout, pos, file_path)