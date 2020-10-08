import itertools

import networkx as nx

from reactor import utils
from reactor.blocks.blockbase import BlockBase
from reactor.const import POSITION, DIRECTION


MIN_LENGTH = 1
MAX_LENGTH = 3


class NodeBlock(BlockBase):

    @property
    def node(self):
        return list(self.data)[0]

    def get_permutations(self):

        # Collect valid step direction and lengths.
        dirs = self.get_start_direction_permutations()
        lengths = range(MIN_LENGTH, MAX_LENGTH + 1)

        # Create permutations from direction and length values.
        perms = []
        p_node = self.pfoo
        p_pos = self.layout.nodes[p_node][POSITION]
        for dir_, length in itertools.product(dirs, lengths):
            g = nx.DiGraph()
            g.add_edge(p_node, self.node, **{DIRECTION: dir_})
            g.nodes[p_node][POSITION] = p_pos
            g.nodes[self.node][POSITION] = p_pos + utils.step(dir_, length)
            perms.append(g)
        return perms