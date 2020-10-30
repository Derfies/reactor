import abc
import itertools
import random

from reactor import utils
from reactor.const import DIRECTION, Direction


class LayouterBase(object):

    __metaclass__ = abc.ABCMeta

    def __init__(self, data, layout):
        self.data = data
        self.current_perm = None
        self.permutations = None
        self.layout = layout

    @property
    def done(self):
        return self.current_perm is not None

    @abc.abstractmethod
    def get_permutations(self):
        """"""

    def init_permutations(self):
        if self.permutations is None:
            self.permutations = self.get_permutations()
            random.shuffle(self.permutations)

    def get_start_direction_permutations(self):

        # Calculate valid edge directions.
        # Remove prev edge direction.
        # Remove sibling edge directions.
        dirs = set(Direction)
        for in_edge in self.layout.in_edges(self.data.root):
            dir = Direction.opposite(self.layout.edges[in_edge][DIRECTION])
            dirs.discard(dir)
        for out_edge in self.layout.out_edges(self.data.root):
            dirs.discard(self.layout.edges[out_edge].get(DIRECTION))
        return dirs

    def can_lay_out(self, perm):

        # Create the list of edges to test collision against. Discard any edge
        # that shares at least one node - this stops edges from intersecting
        # with themselves (in the case of adjacent faces) and edges from
        # intersecting with their parents (in the edge of contiguous edges).
        test_edges = set(self.layout.edges)
        for e1, e2 in itertools.product(perm.edges, self.layout.edges):
            if set(e1) & set(e2):

                # BUG - Won't stop faces with hairpin turns. See space hulk
                # IE faces with colinear edges that aren't adjacent.
                test_edges.discard(e2)

        for e1, e2 in itertools.product(perm.edges, test_edges):
            r1 = utils.get_edge_rect(perm, e1)
            r2 = utils.get_edge_rect(self.layout, e2)
            if r1.intersects(r2):
                return False

        return True

    def add_to_layout(self, perm):
        self.layout.update(perm)
        self.current_perm = perm

    def remove_from_layout(self):
        self.layout.remove_edges_from(self.data.edges)
        rem_nodes = []
        for node in self.data:
            if not self.layout.in_edges(node) and not self.layout.out_edges(node):
                rem_nodes.append(node)
        self.layout.remove_nodes_from(rem_nodes)
        self.current_perm = None
