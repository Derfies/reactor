import itertools
import random

import networkx as nx

from .. import utils
from ..rect import Rect
from ..vector import Vector2
from ..const import POSITION, Direction, DIRECTION
from layouterbase import LayouterBase


MIN_STEP = 1
MAX_STEP = 3


class TreeLayouter(LayouterBase):

    def __init__(self, g, layout=None, root_node=None):
        #super(TreeLayouter, self).__init__()

        self._g = g


        self._root_node = root_node

        self.input = nx.dfs_tree(self._g, self.root_node)
        self.max_iter = 70
        if layout is None:
            layout = nx.DiGraph()
        self.layout = layout
        self.idx = 0

        # Make sure each node is max incident of 4.
        for node in self.input.nodes():
            node_edges = self.input.edges(node)
            assert len(node_edges) < 5, 'Node: {} has incident value greater than 4'.format(node)

    @property
    def root_node(self):
        if self._root_node is None:
            self._root_node = list(self._g.nodes())[0]
        return self._root_node

    @property
    def layouts(self):
        return [self.layout]

    @classmethod
    def from_file(cls, grid_path):
        g = nx.Graph(nx.read_graphml(grid_path))
        return cls(g)

    def intersects_graph2(self, p1, p2, edges):

        r1 = Rect(p1, p2)
        r1.normalise()

        # Does edge intersect the rest of the graph??
        for edge in edges:

            p3 = self.layout.nodes[edge[0]].get(POSITION)
            p4 = self.layout.nodes[edge[1]].get(POSITION)

            if p3 is None or p4 is None:
                #print '        skip:', edge
                continue

            r2 = Rect(p3, p4)
            r2.normalise()
            touches = r1.touches(r2)
            #print '        ', touches, edge, p1, p2, '->', p3, p4
            if touches:
                return r2

        return False

    def _process_node(self, node, p_node):

        print 'process:', node, 'parent:', p_node

        p_pos = Vector2(0, 0)
        dirs = set(Direction)
        edges = set(self.layout.edges())

        if p_node is not None:

            # Remove prev edge direction.
            for in_edge in self.layout.in_edges(p_node):
                dir = Direction.opposite(self.layout.edges[in_edge][DIRECTION])
                dirs.discard(dir)
                edges.discard(in_edge)

            # Remove sibling edge directions.
            for out_edge in self.layout.out_edges(p_node):
                dirs.discard(self.layout.edges[out_edge].get(DIRECTION))
                edges.discard(out_edge)

            p_pos = self.layout.nodes[p_node][POSITION]

        # If the edge intersects with an existing edge we need to shorten the
        # step length, then potentially change the step direction and trying
        # again.
        dirs = list(dirs)
        random.shuffle(dirs)
        steps = range(MIN_STEP, MAX_STEP + 1)
        random.shuffle(steps)

        # TODO:
        # All edges might not be checking all valid directions...
        result = False
        for dir_, step in itertools.product(dirs, steps):
            pos = p_pos + utils.step(dir_, step)
            inter = self.intersects_graph2(p_pos, pos, edges)
            if inter:
                print '        ********** step FAILED:', dir_, step, p_pos, pos, str(inter), edges
                continue

            print '    {} parent:'.format(node), p_node
            print '    {} dir_:'.format(node), dir_
            print '    {} step:'.format(node), step
            print '    {} pos:'.format(node), pos

            if p_node is not None:
                self.layout.add_edge(p_node, node)
            else:
                self.layout.add_node(node)
            self.layout.nodes[node][POSITION] = pos
            if (p_node, node) in self.layout.edges():
                self.layout.edges[(p_node, node)][DIRECTION] = dir_

            neigh_results = []
            for neigh in self.input.neighbors(node):

                neigh_result = self._process_node(neigh, node)
                neigh_results.append(neigh_result)

                # If a neighbor failed to be placed, remove the entire subgraph
                if not neigh_result:
                    print 'remove subgraph:', list(nx.dfs_tree(self.layout, node).nodes())#.copy()
                    self.layout.remove_nodes_from(nx.dfs_tree(self.layout, node))
                    break
            result = all(neigh_results)
            if result:
                break
        else:
            print '######## {} TOTALLY FAILED!!'.format(node)

        print '    {} overall result:'.format(node), result

        # If we can't place all successors then we have to mark this node as
        # failed, which will result in the entire branch being removed and
        # another direction / step value being attempted.
        return result


    def run(self):
        print 'Running:', self

        # Set the root node's position to the origin


        p_node = None
        if self.root_node in self.layout:

            # Assume the root node has already been laid out.
            p_node = next(self.layout.predecessors(self.root_node), None)
        else:

            # Set the start node to 0, 0
            self.layout.add_node(self.root_node)
            self.layout.nodes[self.root_node][POSITION] = Vector2(0, 0)

        for neigh in self.input.neighbors(self.root_node):
            self._process_node(neigh, self.root_node)