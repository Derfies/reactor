import numpy as np
np.random.seed(59)

from reactor.mapgenerator import MapGenerator


# Remaining fails:
# bow1
# single_node1
#GRID_PATH = 'data/angle_wave1.gexf'
GRID_PATH = 'data/test2.gexf'


if __name__ == '__main__':
    gen = MapGenerator(GRID_PATH)
    map_ = gen.run()

    #utils.draw_map(map_)
