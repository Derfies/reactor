import random
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
        return self.data

    def get_permutations(self):

        # Collect valid step direction and lengths.
        dirs = self.calculate_start_direction_permutations()
        lengths = range(MIN_LENGTH, MAX_LENGTH + 1)

        # Create permutations from direction and length values.
        perms = []
        p_node = self.parent_block_node
        p_pos = self.layout.nodes[p_node][POSITION]
        for dir_, length in itertools.product(dirs, lengths):
            g = nx.DiGraph()
            g.add_edge(p_node, self.node, **{DIRECTION: dir_})
            nx.set_node_attributes(g, {
                p_node: {POSITION: p_pos},
                self.node: {POSITION: p_pos + utils.step(dir_, length)}
            })
            perms.append(g)

        # Shuffle result and return.
        random.shuffle(perms)
        return perms