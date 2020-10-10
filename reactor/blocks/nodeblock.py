import itertools

import networkx as nx

from reactor import utils
from reactor.blocks.blockbase import BlockBase
from reactor.const import POSITION, DIRECTION


MIN_LENGTH = 1
MAX_LENGTH = 3


class NodeBlock(BlockBase):

    def get_permutations(self):

        # Collect valid step direction and lengths.
        dirs = self.get_start_direction_permutations()
        lengths = range(MIN_LENGTH, MAX_LENGTH + 1)

        # Create permutations from direction and length values.
        perms = []
        node = list(self.data)[0]
        p_pos = self.layout.nodes[self.p_node][POSITION]
        for dir_, length in itertools.product(dirs, lengths):
            g = nx.DiGraph()
            g.add_edge(self.p_node, node, **{DIRECTION: dir_})
            g.nodes[self.p_node][POSITION] = p_pos
            g.nodes[node][POSITION] = p_pos + utils.step(dir_, length)
            perms.append(g)
        return perms