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
        layouter = layouter_cls(block, self.bg.q, self.layout)

        print '\nprocess:', layouter, ', parent:', layouter.parent_block_node#, 'node:', layouter.node

        result = False
        old_layout = copy.deepcopy(self.layout)
        for perm in layouter.get_permutations():

            # Test to see if the block can be laid out. If so, merge into main
            # layout.
            if not layouter.can_lay_out(perm):
                print '    **** FAILED:', nx.get_node_attributes(perm, POSITION)
                continue
            print '    **** SUCCESS:', nx.get_node_attributes(perm, POSITION)
            layouter.update_layout(perm)

            # Recurse children.
            child_results = []
            for child in self.bg.q.successors(block):

                # If a child failed to be placed, remove the entire subgraph.
                child_result = self._process_block(child)
                child_results.append(child_result)
                if not child_result:

                    # TODO: Need to specialise this... if a face fails then the
                    # parent root node will be removed...
                    # Actually, why - when a face fails and we remove the parent
                    # node, does the parent not not get re-placed?
                    # TODO: Must do block removal - particularly by face
                    print '**** REMOVE SUBGRAPH FROM:', layouter
                    self.layout = layouter.layout = old_layout
                    break

            # All children be laid out, so we can stop looping this block's
            # permutations.
            result = all(child_results)
            if result:
                break

        if not result:
            print '#### TOTALLY FAILED: {}'.format(block)

            # import utils
            # pos = nx.get_node_attributes(self.layout, POSITION)
            # utils.draw(self.layout, pos)

        return result

    def _process_block2(self, block):
        print 'process:', block, self.bg.q.nodes[block].get('cls')

        for child in self.bg.q.successors(block):
            self._process_block2(child)

    def run(self):
        print ''
        self.bg = BlockGraph(self.g)
        self.bg.run()
        self._process_block(self.bg.root)
        print 'complete:', len(self.g) == len(self.layout)

