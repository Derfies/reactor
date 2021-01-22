import random
random.seed(0)

from reactor import utils
from reactor.mapgenerator import MapGenerator


# Remaining fails:
# bow1
# single_node1
GRID_PATH = 'data/tier_test.gexf'


if __name__ == '__main__':
    gen = MapGenerator(GRID_PATH)
    map_ = gen.run()
    #utils.draw_map(map_)
