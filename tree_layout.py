import random
random.seed(1)

import networkx as nx
import matplotlib.pyplot as plt

import utils
from vector import Vector2
from const import POSITION, Direction, DIRECTION


MIN_STEP = 1
MAX_STEP = 3
GRID_PATH = 'data/tree1.graphml'


class MapGenerator(object):

    def __init__(self, grid_path):
        g = nx.Graph(nx.read_graphml(grid_path))
        self.g = nx.dfs_tree(g, list(g.nodes())[0])
        self.idx = 0

        # Make sure each node is max incident of 4.
        for node in self.g.nodes():
            node_edges = self.g.edges(node)
            assert len(node_edges) < 5, 'Node: {} has incident value greater than 4'.format(node)

    def _process_node(self, node, parent, prev_dir):
        print 'process:', node

        position = Vector2(0, 0)
        dir_ = None
        if parent is not None:
            position = self.g.nodes[parent][POSITION]

            print '    parent:', parent

            dirs = nx.get_edge_attributes(map_gen.g, DIRECTION)
            print '    all dirs:', dirs.items()





            dirs2 = dict(filter(lambda x: x[0][0] == parent, dirs.items()))
            print '    dirs2:', dirs2


            dirs3 = dict(filter(lambda x: x[0][1] == parent, dirs.items()))
            print '    dirs3:', dirs3
            dirs3 = {
                k: Direction.opposite(v) for k, v in dirs3.items()
            }

            print '    dirs3 (backward):', dirs3


            dirs2.update(dirs3)

            print '    final:', dirs2


            directions = list(set(Direction) - set(dirs2.values()))



            print '    prev:', prev_dir
            print '    directions:', directions

            dir_ = utils.get_random_direction(directions)
            length = random.randint(MIN_STEP, MAX_STEP)

            print '    length:', length
            new_pos = utils.step(dir_, length)
            position = position + new_pos
        print '    dir_:', dir_
        print '    position:', position
        self.g.nodes[node][POSITION] = position

        if parent is not None:
            self.g.edges[(parent, node)][DIRECTION] = dir_



        for neigh in self.g.neighbors(node):

            # self.idx += 1
            # if self.idx > 10:
            #     return

            self._process_node(neigh, node, dir_)



    def run(self):

        nodes = list(self.g.nodes())
        self._process_node(nodes[0], None, None)

        # HAX
        for node in self.g.nodes():
            if self.g.nodes[node].get(POSITION) is None:
                self.g.nodes[node][POSITION] = Vector2(-5, -5)

        # foo = self.g)
        #
        # print '-->', foo



if __name__ == '__main__':

    # Initialise a map generator using a path to a node graph file, then run it.
    map_gen = MapGenerator(GRID_PATH)
    map_gen.run()

    pos = nx.get_node_attributes(map_gen.g, POSITION)
    nx.draw_networkx(map_gen.g, pos)
    plt.show()