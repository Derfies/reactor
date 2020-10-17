import itertools

import networkx as nx

from reactor import utils
from reactor.layouters.layouterbase import LayouterBase
from reactor.const import POSITION, DIRECTION


MIN_LENGTH = 1
MAX_LENGTH = 3


class EdgeLayouter(LayouterBase):

    def get_permutations(self, layout):

        # Collect valid step direction and lengths.
        dirs = self.get_start_direction_permutations(layout)
        lengths = range(MIN_LENGTH, MAX_LENGTH + 1)

        # Create permutations from direction and length values.
        head, tail = self.data.edge
        p_pos = layout.nodes[head][POSITION]
        perms = []
        for dir_, length in itertools.product(dirs, lengths):
            g = nx.DiGraph()
            g.add_edge(head, tail, **{DIRECTION: dir_})
            g.nodes[head][POSITION] = p_pos
            g.nodes[tail][POSITION] = p_pos + utils.step(dir_, length)
            perms.append(g)
        return perms
