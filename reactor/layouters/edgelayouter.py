import itertools

import networkx as nx
from simple_settings import settings

from reactor import utils
from reactor.layouters.layouterbase import LayouterBase
from reactor.const import POSITION, DIRECTION


class EdgeLayouter(LayouterBase):

    def get_permutations(self, layout):

        # Collect valid step direction and lengths.
        dirs = self.get_start_direction_permutations(layout)
        lengths = range(settings.MIN_LENGTH, settings.MAX_LENGTH + 1)

        # Create permutations from direction and length values.
        head, tail = self.data.edge
        p_pos = layout.nodes[head][POSITION]
        perms = []
        for dir_, length in itertools.product(dirs, lengths):
            perm = nx.DiGraph()
            edge_data = dict(self.data.edge_data, **{DIRECTION: dir_})
            perm.add_edge(head, tail, **edge_data)
            perm.nodes[head][POSITION] = p_pos
            perm.nodes[tail][POSITION] = p_pos + utils.step(dir_, length)
            perms.append(perm)
        return perms
