import random
random.seed(1)

from reactor.mapgenerator import MapGenerator


GRID_PATH = 'data/tree1.graphml'


if __name__ == '__main__':

    # Initialise a map generator using a path to a node graph file, then run it.
    map_gen = MapGenerator(GRID_PATH)
    map_gen.run()