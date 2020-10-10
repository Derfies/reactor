import copy
import random

import networkx as nx

from reactor.blocks.blockgraph import BlockGraph
from reactor.const import POSITION
from reactor.orthogonallayout import OrthogonalLayout
from reactor import utils


class Layouter(object):

    def __init__(self, g):
        self._g = g

        # TODO: In order to make truly abstract, need to make layout and block
        # graphs input args...
        self.layout = OrthogonalLayout()
        self.bg = BlockGraph(self._g)

    def _process_block(self, block):
        result = False
        perms = block.get_permutations()
        random.shuffle(perms)
        for perm in perms:

            # Early-ing out when a child fails waaaaaaaay too early
            old_layout = copy.deepcopy(self.layout)
            if not block.can_lay_out(perm):
                continue
            block.update_layout(perm)

            # Lay out children. If a single child cannot be laid out we consider
            # this whole block to have failed.
            for child in self.bg.q.successors(block):
                if not self._process_block(child):
                    break
            else:
                result = True

            # Stop evaluating permutations on successful lay out.
            if result:
                break
            else:
                self.layout = old_layout

        return result

    def run(self):

        self.bg.run()

        # TODO: Move this into block graph.
        for node in list(self.bg.q):
            layout_cls = self.bg.get_block_class(node)
            layout = layout_cls(node, self.bg.q, self)
            nx.relabel_nodes(self.bg.q, {node: layout}, copy=False)

        self._process_block(self.bg.root)
        print('complete:', len(self._g) == len(self.layout))

