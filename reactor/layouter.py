import random

import networkx as nx

from reactor.const import POSITION
from reactor.blocks.blockgraph import BlockGraphCreator
from reactor.orthogonallayout import OrthogonalLayout


class Layouter(object):

    def __init__(self, g):
        self._g = g

        # TODO: In order to make truly abstract, need to make layout and block
        # graphs input args...
        self.layout = OrthogonalLayout()

    def bfs(self, g):
        blocks = list(g)
        print('blocks:')
        for b in blocks:
            print('    ->', b)

        i = 0
        while i < len(blocks):

            layouter = g.get_layouter(blocks[i])
            if layouter.done:
                print('SKIPPING AS DONE:', blocks[i])
                i += 1
                continue

            print('process ->', i, blocks[i], 'parent:', g.parent(blocks[i]))
            if not layouter.permutations:# is None:
                print('    creating new perms')
                layouter.permutations = layouter.get_permutations(self.layout)
                random.shuffle(layouter.permutations)
            else:
                print('    using existing perms')

            while layouter.permutations:
                perm = layouter.permutations.pop(0)
                if not layouter.can_lay_out(perm, self.layout):
                    print('    FAILED:', nx.get_node_attributes(perm, POSITION))
                    continue
                layouter.add_to_layout(perm, self.layout)
                print('    SUCCESS:', list(perm.edges), nx.get_node_attributes(perm, POSITION))
                layouter.done = True

                i += 1
                break
            else:

                # from reactor import utils
                # pos = nx.get_node_attributes(self.layout, POSITION)
                # utils.draw_graph(self.layout, pos)

                # Move the cursor back to the parent.
                parent = g.parent(blocks[i])
                print('BACKTRACK:', blocks[i], 'TO:', parent)
                while blocks[i] != parent:
                    print('    REWIND:', blocks[i], i)
                    i -= 1

                # Mark all blocks under the parent as not done and remove
                # their permutations.
                j = i
                while j < len(blocks):
                    olayouter = g.get_layouter(blocks[j])
                    if olayouter.done:
                        olayouter.done = False
                        if blocks[j] != blocks[i]:
                            olayouter.permutations.clear()# = None
                            print('    REMOVE PERMS:', blocks[j])
                    j += 1

                rem_blocks = nx.dfs_tree(g, blocks[i])
                for block in rem_blocks:
                    olayouter = g.get_layouter(block)
                    olayouter.remove_from_layout(self.layout)

    def run(self):
        self.backtracked = False
        bgc = BlockGraphCreator(self._g)
        bg = bgc.get_block_graph()
        #root = next(filter(lambda n: not bg.in_edges(n), bg))

        self.bfs(bg)
        print('complete:', len(self._g) == len(self.layout))
        print('remainging:', set(self._g) - set(self.layout))

