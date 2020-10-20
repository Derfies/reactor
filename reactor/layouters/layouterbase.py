import abc
import itertools

from reactor import utils
from reactor.geometry.rect import Rect
from reactor.const import DIRECTION, Direction


class LayouterBase(object):

    __metaclass__ = abc.ABCMeta

    def __init__(self, data, g):
        self.data = data
        self.g = g
        self.done = False
        self.permutations = None

    @abc.abstractmethod
    def get_permutations(self, layout):
        """"""

    def get_start_direction_permutations(self, layout):

        # Calculate valid edge directions.
        # Remove prev edge direction.
        # Remove sibling edge directions.
        dirs = set(Direction)
        for in_edge in layout.in_edges(self.data.root):
            dir = Direction.opposite(layout.edges[in_edge][DIRECTION])
            dirs.discard(dir)
        for out_edge in layout.out_edges(self.data.root):
            dirs.discard(layout.edges[out_edge].get(DIRECTION))
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

    def can_lay_out(self, perm, layout):
        return not any([
            self.edge_intersection(e1, perm, e2, layout)
            for e1, e2 in itertools.product(perm.edges, layout.edges)
        ])

    def add_to_layout(self, perm, layout):
        layout.update(perm)

    def remove_from_layout(self, layout):
        layout.remove_edges_from(self.data.edges)
        rem_nodes = []
        for node in self.data:
            if not layout.in_edges(node) and not layout.out_edges(node):
                rem_nodes.append(node)
        layout.remove_nodes_from(rem_nodes)
