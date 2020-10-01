import copy

import networkx as nx

from reactor.blocks.blockgraph import BlockGraph
from reactor.const import POSITION
from reactor.orthogonalgraph import OrthogonalGraph


class Layouter(object):

    def __init__(self, g):
        self._g = g

        # TODO: In order to make truly abstract, need to make layout and block
        # graphs input args...
        self.layout = OrthogonalGraph()

    @property
    def g(self):
        return self._g

    def _process_block(self, block):
        layouter_cls = self.bg.get_block_class(block)
        layouter = layouter_cls(block, self.bg.q, self)

        print '\nprocess:', layouter, ', parent:', layouter.parent_block_node

        result = False

        for perm in layouter.get_permutations():
            old_layout = copy.deepcopy(self.layout)
            if not layouter.can_lay_out(perm):
                print '    **** FAILED:', nx.get_node_attributes(perm, POSITION), '-> [', list(self.layout), ']'
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
            else:
                print '#### PERM FAILED: {}'.format(block)
                print '    resetting to:', list(old_layout)
                self.layout = old_layout

        print 'leaving:', layouter, ', result:', result, '\n'
        return result

    def run(self):
        print ''
        self.bg = BlockGraph(self.g)
        self.bg.run()
        self._process_block(self.bg.root)
        print 'complete:', len(self.g) == len(self.layout)

