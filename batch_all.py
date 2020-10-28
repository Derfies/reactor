import os
import random

from reactor import utils
from reactor.mapgenerator import MapGenerator


NUM_PERMUTATIONS = 20
DIR_PATH = 'data'
GRID_EXTN = '.gexf'

KNOWN_ISSUES = ['bow1', 'single_node1', 'wrong_degree1']


if __name__ == '__main__':
    all_names = os.listdir(DIR_PATH)
    grid_names = filter(lambda x: os.path.splitext(x)[-1] == GRID_EXTN, all_names)
    ok_names = list(filter(lambda x: os.path.splitext(x)[0] not in KNOWN_ISSUES, grid_names))

    ok_names = ok_names[ok_names.index('tree3.gexf'):]
    for grid_name in ok_names:
        grid_path = os.path.join(DIR_PATH, grid_name)
        for i in range(NUM_PERMUTATIONS):

            # Set random seed and run map generator.
            random.seed(i)
            gen = MapGenerator(grid_path)
            try:
                map_ = gen.run()
            except:
                continue

            # Resolve output path name.
            dir_name = os.path.splitext(os.path.split(grid_path)[-1])[0]
            file_name = '{0:03d}'.format(i)
            file_path = os.path.join('output', dir_name, file_name) + '.png'

            # Save map to file.
            print('saving:', file_path)
            utils.draw_map(map_, file_path)
