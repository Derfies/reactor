import copy
import random

import networkx as nx

from reactor.blocks.blockgraph import BlockGraph
from reactor.const import POSITION
from reactor.orthogonalgraph import OrthogonalGraph
from reactor import utils


class Layouter(object):

    def __init__(self, g):
        self._g = g

        # TODO: In order to make truly abstract, need to make layout and block
        # graphs input args...
        self.layout = OrthogonalGraph()

    def _process_block(self, block):
        print('')
        #print('\nblock:', block)
        #layouter_cls = self.bg.get_block_class(block)
        layouter = block#layouter_cls(block, self.bg.q, self)

        print('process:', layouter, 'parent:', layouter.parent_block_node)

        result = False

        perms = layouter.get_permutations()
        print('    num perms:', len(perms))
        random.shuffle(perms)
        for perm in perms:

            print('    perm:', nx.get_node_attributes(perm, POSITION))
            print('    layout:', nx.get_node_attributes(self.layout, POSITION))

            # Early-ing out when a child fails waaaaaaaay too early
            old_layout = copy.deepcopy(self.layout)
           # coll = layouter.collides(perm)
            if not layouter.can_lay_out(perm):
                print('    **** FAILED:', nx.get_node_attributes(perm, POSITION), '-> [', list(self.layout), ']')
                #print(coll)
                continue
            print('    **** SUCCESS:', nx.get_node_attributes(perm, POSITION))

            layouter.update_layout(perm)
            print('    now:', nx.get_node_attributes(self.layout, POSITION))

            layout = self.layout
            # pos = nx.get_node_attributes(self.layout, POSITION)
            # utils.draw_graph(self.layout, pos)

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
                print('#### PERM FAILED: {}'.format(block))
                #print('    resetting to:', list(old_layout))
                self.layout = old_layout

        print('leaving:', layouter, ', result:', result, '\n')
        return result

    def run(self):
        print('')
        self.bg = BlockGraph(self._g)
        self.bg.run()
        #print('order:', list(nx.dfs_preorder_nodes(self.bg.q, self.bg.root)))
        print('')

        for node in list(self.bg.q):
            layout = self.bg.q.nodes[node]['class'](node, self.bg.q, self)
            nx.relabel_nodes(self.bg.q, {node: layout}, copy=False)

        print('FINAL')
        for node in list(self.bg.q):
            print(node, type(node))#, '->', self.q.nodes[node].get(LAYOUT_CLASS))
        print('************')
        self._process_block(self.bg.root)
        print('complete:', len(self._g) == len(self.layout))

