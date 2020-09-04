import itertools
import random
random.seed(2)

import networkx as nx
import matplotlib.pyplot as plt

import utils
from rect import Rect
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

    def intersects_graph2(self, p1, p2, edges):

        r1 = Rect(p1, p2)
        r1.normalise()

        # Does edge intersect the rest of the graph??
        for edge in edges:

            p3 = self.g.nodes[edge[0]].get(POSITION)
            p4 = self.g.nodes[edge[1]].get(POSITION)

            if p3 is None or p4 is None:
                #print '        skip:', edge
                continue

            r2 = Rect(p3, p4)
            r2.normalise()
            touches = r1.touches(r2)
            #print '        ', touches, edge, p1, p2, '->', p3, p4
            if touches:
                return True

        return False

    def _process_node(self, edge, p_edge):

        # self.idx += 1
        # if self.idx > 25:
        #     print '    {} early out - True'.format(edge[1])
        #     return True

        print 'process:', edge[1]


        dirs = set(Direction)
        edges = set(self.g.edges())

        # Remove prev edge direction.
        if p_edge[0] is not None:
            p_dir = Direction.opposite(self.g.edges[p_edge][DIRECTION])
            dirs.discard(p_dir)
            edges.discard(p_edge)

        # Remove sibling edge directions.
        s_edges = filter(lambda e: e[0] == edge[0], self.g.edges())
        for s_edge in s_edges:
            dirs.discard(self.g.edges[s_edge].get(DIRECTION))
            edges.discard(s_edge)

        # If the edge intersects with an existing edge we need to shorten the
        # step length, then potentially change the step direction and trying
        # again.
        dirs = list(dirs)
        random.shuffle(dirs)
        max_step = random.randint(MIN_STEP, MAX_STEP)

        # TODO: Make this properly random.
        steps = reversed(range(MIN_STEP, max_step + 1))

        p_pos = Vector2(0, 0)#, Vector2(0, 0)
        if edge[0] in self.g.nodes:
            p_pos = self.g.nodes[edge[0]][POSITION]

        result = False
        for dir_, step in itertools.product(dirs, steps):
            pos = p_pos + utils.step(dir_, step)
            inter = self.intersects_graph2(p_pos, pos, edges)
            if inter:
                print '        ********** step FAILED:', dir_, step, p_pos, pos
                continue

            print '    {} parent:'.format(edge[1]), edge[0]
            print '    {} dir_:'.format(edge[1]), dir_
            print '    {} step:'.format(edge[1]), step
            print '    {} pos:'.format(edge[1]), pos

            self.g.nodes[edge[1]][POSITION] = pos
            if edge in self.g.edges():
                self.g.edges[edge][DIRECTION] = dir_

            neigh_results = []
            for neigh in self.g.neighbors(edge[1]):



                neigh_result = self._process_node((edge[1], neigh), edge)
                neigh_results.append(neigh_result)
                if not neigh_result:
                    # del self.g.nodes[edge[1]][POSITION]
                    # if edge in self.g.edges():
                    #     del self.g.edges[edge][DIRECTION]
                    # print '    >>> {} removing data...'.format(edge[1])
                    break

            result = all(neigh_results)
            if result:
                break


        else:
            print '######## {} TOTALLY FAILED!!'.format(edge[1])

        print '    {} overall result:'.format(edge[1]), result

        return result


    def run(self):

        nodes = list(self.g.nodes())
        self._process_node((None, nodes[0]), (None, None))

        for node in map_gen.g.nodes():
            if map_gen.g.nodes[node].get(POSITION) is None:
                map_gen.g.nodes[node][POSITION] = Vector2(-5, -5)


if __name__ == '__main__':

    # Initialise a map generator using a path to a node graph file, then run it.
    map_gen = MapGenerator(GRID_PATH)
    try:
        map_gen.run()
    except Exception, e:

        # HAX
        for node in map_gen.g.nodes():
            if map_gen.g.nodes[node].get(POSITION) is None:
                map_gen.g.nodes[node][POSITION] = Vector2(-5, -5)

        raise

    pos = nx.get_node_attributes(map_gen.g, POSITION)
    nx.draw_networkx(map_gen.g, pos)
    plt.show()

    raise