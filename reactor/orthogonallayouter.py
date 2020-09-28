import copy

import networkx as nx

from reactor.blocks.blockgraph import BlockGraph
from reactor.const import POSITION
from reactor.orthogonalgraph import OrthogonalGraph


class OrthogonalLayouter(object):

    def __init__(self, g):
        self._g = g

        self.layout = OrthogonalGraph()

    @property
    def g(self):
        return self._g

    def _process_block(self, block):
        layouter_cls = self.bg.get_block_class(block)
        layouter = layouter_cls(block, self.bg.q, self)

        print '\nprocess:', layouter, ', parent:', layouter.parent_block_node

        result = False
        old_layout = copy.deepcopy(self.layout)
        for perm in layouter.get_permutations():
            if not layouter.can_lay_out(perm):
                print '    **** FAILED:', nx.get_node_attributes(perm, POSITION)
                continue
            print '    **** SUCCESS:', nx.get_node_attributes(perm, POSITION)
            layouter.update_layout(perm)

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

        # Layout failed - revert the layout.
        if not result:
            print '#### TOTALLY FAILED: {}'.format(block)
            self.layout = old_layout

        return result

    def run(self):
        print ''
        self.bg = BlockGraph(self.g)
        self.bg.run()
        self._process_block(self.bg.root)
        print 'complete:', len(self.g) == len(self.layout)

