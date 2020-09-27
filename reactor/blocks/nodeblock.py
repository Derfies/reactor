import random
import itertools

import networkx as nx

from reactor import utils
from reactor.blocks.blockbase import BlockBase
from reactor.const import POSITION, DIRECTION, Direction


MIN_STEP = 1
MAX_STEP = 3


class NodeBlock(BlockBase):

    @property
    def node(self):
        return self.data

    def get_permutations(self):

        # If no parent node has been laid out then this block is the first.
        p_node = self.parent_block_node

        # Calculate valid edge directions.
        # Remove prev edge direction.
        # Remove sibling edge directions.
        dirs = set(Direction)
        for in_edge in self.layout.in_edges(p_node):
            dir = Direction.opposite(self.layout.edges[in_edge][DIRECTION])
            dirs.discard(dir)
        for out_edge in self.layout.out_edges(p_node):
            dirs.discard(self.layout.edges[out_edge].get(DIRECTION))

        # Shuffle available directions and step lengths.
        dirs = list(dirs)
        random.shuffle(dirs)
        steps = range(MIN_STEP, MAX_STEP + 1)
        random.shuffle(steps)

        # Create permutations from the direction and step values.
        perms = []
        p_pos = self.layout.nodes[p_node][POSITION]
        # print 'dirs:', dirs
        # print 'steps:', steps
        # print 'perm:', list(itertools.product(dirs, steps))
        for dir_, step in itertools.product(dirs, steps):
            g = nx.DiGraph()
            g.add_edge(p_node, self.node, **{DIRECTION: dir_})
            nx.set_node_attributes(g, {
                p_node: {POSITION: p_pos},
                self.node: {POSITION: p_pos + utils.step(dir_, step)}
            })
            perms.append(g)
        return perms