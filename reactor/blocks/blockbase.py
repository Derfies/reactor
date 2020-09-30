import abc
import itertools

from reactor import utils
from reactor.geometry.rect import Rect
from reactor.const import DIRECTION, Direction


class BlockBase(object):

    __metaclass__ = abc.ABCMeta

    def __init__(self, data, q, layouter):
        self.data = data
        self.q = q
        self.layouter = layouter

    @property
    def layout(self):
        return self.layouter.layout

    def __str__(self):
        return self.__class__.__name__ + '.' + str(self.data)

    @property
    def parent_block_node(self):
        return next(self.q.predecessors(self.data), None)

    @abc.abstractmethod
    def get_permutations(self):
        """"""

    def calculate_start_direction_permutations(self):

        # Calculate valid edge directions.
        # Remove prev edge direction.
        # Remove sibling edge directions.
        dirs = set(Direction)
        for in_edge in self.layout.in_edges(self.parent_block_node):
            dir = Direction.opposite(self.layout.edges[in_edge][DIRECTION])
            dirs.discard(dir)
        for out_edge in self.layout.out_edges(self.parent_block_node):
            dirs.discard(self.layout.edges[out_edge].get(DIRECTION))
        return dirs

    def edge_intersection(self, e1, g1, e2, g2):
        """
        Still has a weird smell about it. If the edges being compared share a
        node then do an intersection test, otherwise do a touch test.

        TODO: Move to utils?

        """
        r1 = Rect(*utils.get_edge_positions(g1, e1))
        r1.normalise()
        r2 = Rect(*utils.get_edge_positions(g2, e2))
        r2.normalise()
        return r1.intersects(r2) if set(e1) & set(e2) else r1.touches(r2)

    def can_lay_out(self, perm):
        return not any([
            self.edge_intersection(e1, perm, e2, self.layout)
            for e1, e2 in itertools.product(perm.edges(), self.layout.edges())
        ])

    def update_layout(self, g):
        self.layout.update(g)