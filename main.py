import random
random.seed(0)

from reactor.mapgenerator import MapGenerator


# Remaining fails:
# bow1
# single_node1
# tree_and_cycle2 (needs leading edge permutations)
GRID_PATH = 'data/tree_and_cycle2.graphml'


if __name__ == '__main__':

    # Initialise a map generator using a path to a node graph file, then run it.
    gen = MapGenerator(GRID_PATH)
    gen.run()