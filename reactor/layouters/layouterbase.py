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

    def can_lay_out(self, perm, map_):

        # Create the list of edges to test collision against. Discard any edge
        # that shares at least one node - this stops edges from intersecting
        # with themselves (in the case of adjacent faces) and edges from
        # intersecting with their parents (in the edge of contiguous edges).
        test_edges = set(map_.layout.edges)
        for e1, e2 in itertools.product(perm.edges, map_.layout.edges):
            if set(e1) & set(e2):
                test_edges.discard(e2)

        for e1, e2 in itertools.product(perm.edges, test_edges):
            r1 = utils.get_edge_rect(perm, e1)
            r2 = utils.get_edge_rect(map_.layout, e2)
            if r1.intersects(r2):
                return False

        return True

    def add_to_layout(self, perm, layout):
        layout.update(perm)

    def remove_from_layout(self, layout):
        layout.remove_edges_from(self.data.edges)
        rem_nodes = []
        for node in self.data:
            if not layout.in_edges(node) and not layout.out_edges(node):
                rem_nodes.append(node)
        layout.remove_nodes_from(rem_nodes)
