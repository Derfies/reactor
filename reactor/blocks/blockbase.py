import abc

from reactor.rect import Rect
from reactor.const import POSITION


class BlockBase(object):

    __metaclass__ = abc.ABCMeta

    def __init__(self, g, q, layout):
        self.g = g
        self.q = q
        self.layout = layout

    @property
    def root_node(self):
        return filter(lambda n: not self.g.in_edges(n), self.g.nodes())[0]

    @property
    def parent_block_node(self):
        return next(self.g._graph.predecessors(self.node), None)

    @property
    def parent(self):
        return next(self.q.predecessors(self), None)

    @abc.abstractmethod
    def get_permutations(self, *args, **kwargs):
        """"""

    @abc.abstractmethod
    def can_lay_out(self, *args, **kwargs):
        """"""

    def intersects_graph2(self, p1, p2, ignore_edges=None):

        ignore_edges = ignore_edges or []

        r1 = Rect(p1, p2)
        r1.normalise()

        # Does edge intersect the rest of the graph??
        edges = set(self.layout.edges()) - set(ignore_edges)
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

    def permutation_intersected(self, perm, edges):
        for edge in perm.edges():
            p1 = perm.nodes[edge[0]].get(POSITION)
            p2 = perm.nodes[edge[1]].get(POSITION)
            if self.intersects_graph2(p1, p2, edges):
                return True
        return False