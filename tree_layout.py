import itertools
import random
random.seed(0)

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

    def does_edge_intersect(self, e1, e2):
        # if None in e1 or None in e2:
        #     return False

        a1 = self.g.nodes[e1[0]].get(POSITION)
        a2 = self.g.nodes[e1[1]].get(POSITION)
        b1 = self.g.nodes[e2[0]].get(POSITION)
        b2 = self.g.nodes[e2[1]].get(POSITION)

        # print a1, a2
        # print b1, b2



        if a1 is None or a2 is None or b1 is None or b2 is None:
            return False

        r1 = Rect(a1, a2)
        r1.normalise()
        r2 = Rect(b1, b2)
        r2.normalise()
        #print '    ', r1.p1, r1.p2, r2.p1, r2.p2
        return r1.touches(r2)

    def intersects_graph(self, edge, pos):

        # Does edge intersect the rest of the graph??
        for e in self.g.edges():
            if edge[0] in e or edge[1] in e:
                print '        skip node: {}'.format(node)
                continue
            inter = self.does_edge_intersect(edge, e)
            if inter:
                print '    ********** intersects:', edge, e, inter
                return True

        return False

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

    def _process_node(self, node, p_node, p_edge):
        print 'process:', node

        edge = (p_node, node)

        print '    edge:', edge
        print '    p_edge:', p_edge

        pos = Vector2(0, 0)
        dir_ = None
        if p_node is not None:

            edges = set(self.g.edges())
            dirs = set(Direction)

            # Remove prev edge direction.
            if p_edge[0] is not None:
                p_dir = Direction.opposite(self.g.edges[p_edge][DIRECTION])
                dirs.discard(p_dir)
                edges.discard(p_edge)

            # Remove sibling edge directions.
            s_edges = filter(lambda x: x[0] == p_node, self.g.edges())
            for s_edge in s_edges:
                dirs.discard(self.g.edges[s_edge].get(DIRECTION))
                edges.discard(s_edge)

            p_pos = self.g.nodes[p_node][POSITION]

            #print '    testing:', edges


            # If the edge intersects with an existing edge we need to shorten the
            # step length, then potentially change the step direction and trying
            # again.
            dirs = list(dirs)
            random.shuffle(dirs)
            max_step = random.randint(MIN_STEP, MAX_STEP)
            steps = reversed(range(MIN_STEP, max_step + 1))
            for d, step in itertools.product(dirs, steps):
                p = p_pos + utils.step(d, step)
                inter = self.intersects_graph2(p_pos, p, edges)
                #print '    inter:', inter#, edges
                if not inter:
                    dir_ = d
                    pos = p
                    break
                else:
                    print '        ********** step FAILED:', d, step, p_pos, p

            self.g.edges[edge][DIRECTION] = dir_

            print '    step:', step



        print '    dir_:', dir_
        print '    position:', pos

        # TODO: Don't yet know this is a valid position
        self.g.nodes[node][POSITION] = pos# + Vector2(random.random() / 2.0, random.random() / 2.0)



        for neigh in self.g.neighbors(node):

            self.idx += 1
            if self.idx > 50:
                return

            self._process_node(neigh, node, edge)

    def run(self):

        nodes = list(self.g.nodes())
        self._process_node(nodes[0], None, None)

        for node in map_gen.g.nodes():
            if map_gen.g.nodes[node].get(POSITION) is None:
                map_gen.g.nodes[node][POSITION] = Vector2(-10, -5)


if __name__ == '__main__':

    # Initialise a map generator using a path to a node graph file, then run it.
    map_gen = MapGenerator(GRID_PATH)
    try:
        map_gen.run()
    except Exception, e:

        # HAX
        for node in map_gen.g.nodes():
            if map_gen.g.nodes[node].get(POSITION) is None:
                map_gen.g.nodes[node][POSITION] = Vector2(-10, -5)

        raise

    pos = nx.get_node_attributes(map_gen.g, POSITION)
    nx.draw_networkx(map_gen.g, pos)
    plt.show()

    raise