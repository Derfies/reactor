import networkx as nx


class Layouter(object):

    def __init__(self, block):
        self.block = block
        self.layout = nx.DiGraph()

    def _process_block(self, block):
        result = True
        for perm in block.get_permutations():

            # Test to see if the block can be laid out. If so, merge into main
            # layout.
            if not block.can_lay_out(perm):
                print '    **** FAILED:', block, perm
                continue
            self.layout.merge(perm)

            # Recurse children.
            for child in block.children:
                child_result = self._process_block(child)

                # If a child failed to be placed, remove the entire subgraph.
                if not child_result:
                    print 'REMOVE SUBGRAPH'
                    self.layout.remove(perm)
                    result = False
                    break

            # All children be laid out, so we can stop looping this block's
            # permutations.
            if result:
                break

        else:
            print '#### TOTALLY FAILED:'.format(block)

        return result

    def run(self):
        self._process_block(self.block)